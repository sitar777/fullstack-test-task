from __future__ import annotations

import os

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("PGPORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test")

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
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


@pytest.fixture
def temp_storage(tmp_path, monkeypatch):
    storage_dir = tmp_path / "files"
    storage_dir.mkdir()
    monkeypatch.setattr("src.config.STORAGE_DIR", storage_dir)
    monkeypatch.setattr("src.services.file_service.STORAGE_DIR", storage_dir)
    monkeypatch.setattr("src.tasks.STORAGE_DIR", storage_dir)
    return storage_dir


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=execute_result)
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock(side_effect=_refresh_model)
    return session


def _refresh_model(obj):
    now = datetime.now(timezone.utc)
    if getattr(obj, "created_at", None) is None:
        obj.created_at = now
    if getattr(obj, "updated_at", None) is None:
        obj.updated_at = now
    if getattr(obj, "requires_attention", None) is None:
        obj.requires_attention = False
    return obj


@pytest.fixture
def mock_session_maker(mock_session, monkeypatch):
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = mock_session
    context_manager.__aexit__.return_value = None

    maker = MagicMock(return_value=context_manager)
    monkeypatch.setattr("src.db.async_session_maker", maker)
    monkeypatch.setattr("src.services.file_service.async_session_maker", maker)
    monkeypatch.setattr("src.services.alert_service.async_session_maker", maker)
    monkeypatch.setattr("src.tasks.async_session_maker", maker)
    return maker, mock_session


@pytest.fixture
async def test_client(mock_session_maker, temp_storage, mocker):
    mocker.patch("src.api.routes.files.process_uploaded_file.delay")

    from src.app import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
