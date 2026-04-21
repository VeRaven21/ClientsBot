from database.models.users.users import Client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.db import get_db


async def add_user(client: Client) -> None:
    db_gen = get_db()
    db: AsyncSession = await db_gen.__anext__()

    db.add(client)
    await db.commit()


async def get_user_by_tg_id(tg_id: int) -> Client | None:
    db_gen = get_db()
    db: AsyncSession = await db_gen.__anext__()

    result = await db.execute(select(Client).where(Client.tg_id == tg_id))
    client = result.fetchone()

    return client[0] if client else None
