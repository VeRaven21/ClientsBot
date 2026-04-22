from core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Worker


async def get_all_workers():
    db_gen = get_db()
    db: AsyncSession = await db_gen.__anext__()

    result = await db.execute(select(Worker))
    return result.scalars().all()