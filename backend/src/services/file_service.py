import mimetypes
from pathlib import Path
from uuid import uuid4

from src.config import STORAGE_DIR
from src.db import async_session_maker
from src.exceptions import FileNotFound, StoredFileNotFound
from src.models import StoredFile
from src.repositories import alert_repository, file_repository


async def list_files() -> list[StoredFile]:
    async with async_session_maker() as session:
        return await file_repository.list_files(session)


async def get_file(file_id: str) -> StoredFile:
    async with async_session_maker() as session:
        file_item = await file_repository.get_by_id(session, file_id)
        if not file_item:
            raise FileNotFound
        return file_item


async def create_file(
    title: str,
    *,
    content: bytes,
    filename: str,
    content_type: str | None = None,
) -> StoredFile:
    file_id = str(uuid4())
    suffix = Path(filename).suffix
    stored_name = f"{file_id}{suffix}"
    stored_path = STORAGE_DIR / stored_name
    stored_path.write_bytes(content)

    file_item = StoredFile(
        id=file_id,
        title=title,
        original_name=filename or stored_name,
        stored_name=stored_name,
        mime_type=content_type or mimetypes.guess_type(stored_name)[0] or "application/octet-stream",
        size=len(content),
        processing_status="uploaded",
    )
    try:
        async with async_session_maker() as session:
            return await file_repository.add(session, file_item)
    except Exception:
        stored_path.unlink(missing_ok=True)
        raise


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
        await alert_repository.delete_by_file_id(session, file_id)
        await file_repository.remove(session, file_item)

    if stored_path.exists():
        stored_path.unlink()


async def get_file_path(file_id: str) -> tuple[StoredFile, Path]:
    file_item = await get_file(file_id)
    stored_path = STORAGE_DIR / file_item.stored_name
    if not stored_path.exists():
        raise StoredFileNotFound
    return file_item, stored_path
