from __future__ import annotations

import os

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("PGPORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test")

from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import UploadFile
from httpx import ASGITransport, AsyncClient

from src.models import Alert, StoredFile


def make_stored_file(
    *,
    file_id: str | None = None,
    title: str = "Test file",
    original_name: str = "test.txt",
    stored_name: str | None = None,
    mime_type: str = "text/plain",
    size: int = 12,
    processing_status: str = "uploaded",
    scan_status: str | None = None,
    scan_details: str | None = None,
    metadata_json: dict | None = None,
    requires_attention: bool = False,
) -> StoredFile:
    file_id = file_id or str(uuid4())
    stored_name = stored_name or f"{file_id}.txt"
    now = datetime.now(timezone.utc)
    return StoredFile(
        id=file_id,
        title=title,
        original_name=original_name,
        stored_name=stored_name,
        mime_type=mime_type,
        size=size,
        processing_status=processing_status,
        scan_status=scan_status,
        scan_details=scan_details,
        metadata_json=metadata_json,
        requires_attention=requires_attention,
        created_at=now,
        updated_at=now,
    )


def make_alert(
    *,
    alert_id: int = 1,
    file_id: str,
    level: str = "info",
    message: str = "File processed successfully",
) -> Alert:
    return Alert(
        id=alert_id,
        file_id=file_id,
        level=level,
        message=message,
        created_at=datetime.now(timezone.utc),
    )


def make_upload_file(
    content: bytes,
    *,
    filename: str = "test.txt",
    content_type: str = "text/plain",
) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers={"content-type": content_type},
    )


@pytest.fixture
def temp_storage(tmp_path, monkeypatch):
    storage_dir = tmp_path / "files"
    storage_dir.mkdir()
    monkeypatch.setattr("src.service.STORAGE_DIR", storage_dir)
    monkeypatch.setattr("src.tasks.STORAGE_DIR", storage_dir)
    return storage_dir


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock(side_effect=lambda obj: obj)
    return session


@pytest.fixture
def mock_session_maker(mock_session, monkeypatch):
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = mock_session
    context_manager.__aexit__.return_value = None

    maker = MagicMock(return_value=context_manager)
    monkeypatch.setattr("src.service.async_session_maker", maker)
    monkeypatch.setattr("src.tasks.async_session_maker", maker)
    return maker, mock_session


@pytest.fixture
async def test_client(mock_session_maker, temp_storage, mocker):
    mocker.patch("src.app.scan_file_for_threats.delay")

    from src.app import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
