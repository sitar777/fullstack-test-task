import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from src.config import STORAGE_DIR
from src.db import async_session_maker
from src.exceptions import EmptyFile, FileNotFound, StoredFileNotFound
from src.models import StoredFile
from src.repositories import file_repository


async def list_files() -> list[StoredFile]:
    async with async_session_maker() as session:
        return await file_repository.list_files(session)


async def get_file(file_id: str) -> StoredFile:
    async with async_session_maker() as session:
        file_item = await file_repository.get_by_id(session, file_id)
        if not file_item:
            raise FileNotFound
        return file_item


async def create_file(title: str, upload_file: UploadFile) -> StoredFile:
    content = await upload_file.read()
    if not content:
        raise EmptyFile

    file_id = str(uuid4())
    suffix = Path(upload_file.filename or "").suffix
    stored_name = f"{file_id}{suffix}"
    stored_path = STORAGE_DIR / stored_name
    stored_path.write_bytes(content)

    file_item = StoredFile(
        id=file_id,
        title=title,
        original_name=upload_file.filename or stored_name,
        stored_name=stored_name,
        mime_type=upload_file.content_type or mimetypes.guess_type(stored_name)[0] or "application/octet-stream",
        size=len(content),
        processing_status="uploaded",
    )
    async with async_session_maker() as session:
        return await file_repository.add(session, file_item)


async def update_file(file_id: str, title: str) -> StoredFile:
    async with async_session_maker() as session:
        file_item = await file_repository.get_by_id(session, file_id)
        if not file_item:
            raise FileNotFound
        file_item.title = title
        return await file_repository.save(session, file_item)


async def delete_file(file_id: str) -> None:
    async with async_session_maker() as session:
        file_item = await file_repository.get_by_id(session, file_id)
        if not file_item:
            raise FileNotFound
        stored_path = STORAGE_DIR / file_item.stored_name
        if stored_path.exists():
            stored_path.unlink()
        await file_repository.delete(session, file_item)


async def get_file_path(file_id: str) -> tuple[StoredFile, Path]:
    file_item = await get_file(file_id)
    stored_path = STORAGE_DIR / file_item.stored_name
    if not stored_path.exists():
        raise StoredFileNotFound
    return file_item, stored_path
