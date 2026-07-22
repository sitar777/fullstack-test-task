from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from tests.conftest import make_stored_file


async def test_list_files_returns_200(test_client, mock_session_maker):
    file_item = make_stored_file()
    _, mock_session = mock_session_maker

    result = MagicMock()
    result.scalars.return_value.all.return_value = [file_item]
    mock_session.execute = AsyncMock(return_value=result)

    response = await test_client.get("/files")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == file_item.id


async def test_create_file_returns_201_and_triggers_scan(test_client, mock_session_maker, mocker):
    delay = mocker.patch("src.app.scan_file_for_threats.delay")

    response = await test_client.post(
        "/files",
        data={"title": "My file"},
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "My file"
    assert payload["processing_status"] == "uploaded"
    delay.assert_called_once_with(payload["id"])


async def test_get_file_404_for_unknown_id(test_client, mock_session_maker):
    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=None)

    response = await test_client.get("/files/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"


async def test_patch_file_updates_title(test_client, mock_session_maker):
    file_item = make_stored_file(title="Old title")
    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)

    response = await test_client.patch(
        f"/files/{file_item.id}",
        json={"title": "New title"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "New title"


async def test_patch_file_422_for_long_title(test_client):
    response = await test_client.patch(
        "/files/00000000-0000-0000-0000-000000000000",
        json={"title": "a" * 256},
    )

    assert response.status_code == 422


async def test_download_file_404_when_missing_on_disk(test_client, mock_session_maker, temp_storage):
    file_item = make_stored_file()
    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)

    response = await test_client.get(f"/files/{file_item.id}/download")

    assert response.status_code == 404
    assert response.json()["detail"] == "Stored file not found"


async def test_delete_file_returns_204(test_client, mock_session_maker, temp_storage):
    file_item = make_stored_file()
    stored_path = temp_storage / file_item.stored_name
    stored_path.write_bytes(b"hello")

    _, mock_session = mock_session_maker
    mock_session.get = AsyncMock(return_value=file_item)

    response = await test_client.delete(f"/files/{file_item.id}")

    assert response.status_code == 204
