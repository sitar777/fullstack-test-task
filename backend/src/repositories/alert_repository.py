from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Alert


async def list_alerts(session: AsyncSession) -> list[Alert]:
    result = await session.execute(select(Alert).order_by(Alert.created_at.desc()))
    return list(result.scalars().all())


async def add(session: AsyncSession, alert: Alert) -> Alert:
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert


async def get_by_file_id(session: AsyncSession, file_id: str) -> Alert | None:
    result = await session.execute(select(Alert).where(Alert.file_id == file_id).limit(1))
    return result.scalars().first()


async def delete_by_file_id(session: AsyncSession, file_id: str) -> None:
    result = await session.execute(select(Alert).where(Alert.file_id == file_id))
    for alert in result.scalars().all():
        await session.delete(alert)
