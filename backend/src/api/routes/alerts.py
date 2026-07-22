from fastapi import APIRouter

from src.schemas import AlertItem
from src.services.alert_service import list_alerts

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[AlertItem])
async def list_alerts_view():
    return await list_alerts()
