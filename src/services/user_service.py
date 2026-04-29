import crud.user_crud as user_crud
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User


async def get_user_by_tg_id(tg_id: int, session: AsyncSession) -> User | None:
    return await user_crud.get_user_by_tg_id(tg_id, session)


async def add_user_to_db(user: User, session: AsyncSession) -> None:
    await user_crud.add_user_to_db(user, session)
