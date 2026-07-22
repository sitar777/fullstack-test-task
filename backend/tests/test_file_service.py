from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.service import create_file, delete_file
from tests.conftest import make_stored_file, make_upload_file


async def test_create_file_rejects_empty_content(mock_session_maker, temp_storage):
    upload = make_upload_file(b"")

    with pytest.raises(HTTPException) as exc_info:
        await create_file(title="Empty", upload_file=upload)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "File is empty"


async def test_create_file_rejects_title_over_255_chars(mock_session_maker, temp_storage):
    upload = make_upload_file(b"hello")

    with pytest.raises((HTTPException, ValueError)):
        await create_file(title="a" * 256, upload_file=upload)


async def test_create_file_cleans_up_disk_on_db_failure(mock_session_maker, temp_storage):
    _, mock_session = mock_session_maker
    mock_session.commit = AsyncMock(side_effect=RuntimeError("db error"))

    upload = make_upload_file(b"hello")

    with pytest.raises(RuntimeError, match="db error"):
        await create_file(title="Test", upload_file=upload)

    assert list(temp_storage.iterdir()) == []


async def test_delete_file_succeeds_when_alerts_exist(mock_session_maker, temp_storage):
    file_item = make_stored_file()
    stored_path = temp_storage / file_item.stored_name
    stored_path.write_bytes(b"hello")

    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)

    deleted_types: list[str] = []

    async def track_delete(obj):
        deleted_types.append(type(obj).__name__)

    mock_session.delete = AsyncMock(side_effect=track_delete)

    await delete_file(file_item.id)

    assert "Alert" in deleted_types
    assert "StoredFile" in deleted_types
    mock_session.commit.assert_awaited_once()
    assert not stored_path.exists()


async def test_delete_file_removes_disk_after_db_commit(mock_session_maker, temp_storage):
    file_item = make_stored_file()
    stored_path = temp_storage / file_item.stored_name
    stored_path.write_bytes(b"hello")

    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)

    commit_calls: list[str] = []

    async def track_commit():
        commit_calls.append("commit")
        if not stored_path.exists():
            commit_calls.append("disk_removed_before_commit")

    mock_session.commit = AsyncMock(side_effect=track_commit)

    await delete_file(file_item.id)

    assert commit_calls == ["commit"]
    assert not stored_path.exists()


async def test_create_file_rejects_over_10mb(mock_session_maker, temp_storage):
    upload = make_upload_file(b"x" * (10 * 1024 * 1024 + 1))

    with pytest.raises(HTTPException) as exc_info:
        await create_file(title="Large", upload_file=upload)

    assert exc_info.value.status_code in {400, 413}
    assert list(temp_storage.iterdir()) == []
