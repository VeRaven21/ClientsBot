from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.db import get_db
from database.models import Service


async def get_all_services():
    db_gen = get_db()
    db: AsyncSession = await db_gen.__anext__()

    result = await db.execute(select(Service))
    return result.scalars().all()