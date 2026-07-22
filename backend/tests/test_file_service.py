from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.file_service import create_file, delete_file
from tests.conftest import make_alert, make_stored_file


async def test_create_file_cleans_up_disk_on_db_failure(mock_session_maker, temp_storage):
    _, mock_session = mock_session_maker
    mock_session.commit = AsyncMock(side_effect=RuntimeError("db error"))

    with pytest.raises(RuntimeError, match="db error"):
        await create_file(
            title="Test",
            content=b"hello",
            filename="test.txt",
            content_type="text/plain",
        )

    assert list(temp_storage.iterdir()) == []


async def test_delete_file_succeeds_when_alerts_exist(mock_session_maker, temp_storage):
    file_item = make_stored_file()
    alert = make_alert(file_id=file_item.id)
    stored_path = temp_storage / file_item.stored_name
    stored_path.write_bytes(b"hello")

    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)

    alert_result = MagicMock()
    alert_result.scalars.return_value.all.return_value = [alert]
    mock_session.execute = AsyncMock(return_value=alert_result)

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
