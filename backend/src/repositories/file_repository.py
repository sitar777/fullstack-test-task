from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import StoredFile


async def list_files(session: AsyncSession) -> list[StoredFile]:
    result = await session.execute(select(StoredFile).order_by(StoredFile.created_at.desc()))
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, file_id: str) -> StoredFile | None:
    return await session.get(StoredFile, file_id)


async def add(session: AsyncSession, file_item: StoredFile) -> StoredFile:
    session.add(file_item)
    await session.commit()
    await session.refresh(file_item)
    return file_item


async def save(session: AsyncSession, file_item: StoredFile) -> StoredFile:
    await session.commit()
    await session.refresh(file_item)
    return file_item


async def delete(session: AsyncSession, file_item: StoredFile) -> None:
    await session.delete(file_item)
    await session.commit()
