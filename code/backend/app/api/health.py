from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.config import get_settings, Settings

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    db_status = "connected"
    db_error = ""
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "disconnected"
        db_error = str(e)

    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_status,
        "db_error": db_error
    }
