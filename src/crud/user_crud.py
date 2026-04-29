from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User


async def get_user_by_tg_id(tg_id: int, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalars().first()
    return user


async def add_user_to_db(user: User, session: AsyncSession) -> None:
    session.add(user)
    await session.commit()
