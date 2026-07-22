from src.db import async_session_maker
from src.models import Alert
from src.repositories import alert_repository


async def list_alerts() -> list[Alert]:
    async with async_session_maker() as session:
        return await alert_repository.list_alerts(session)
