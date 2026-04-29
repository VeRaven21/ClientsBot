from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, UserRoleEnum


async def get_user_by_tg_id(tg_id: int, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalars().first()
    return user


async def add_user_to_db(user: User, session: AsyncSession) -> None:
    session.add(user)
    await session.commit()


async def get_users_stats(session: AsyncSession) -> dict:
    """Получить статистику пользователей по ролям"""
    # Получаем количество пользователей по ролям
    result = await session.execute(
        select(User.role, func.count(User.id)).group_by(User.role)
    )
    stats = dict(result.all())

    # Получаем общее количество
    total_result = await session.execute(select(func.count(User.id)))
    total = total_result.scalar()

    return {
        "total": total,
        "clients": stats.get(UserRoleEnum.CLIENT, 0),
        "workers": stats.get(UserRoleEnum.WORKER, 0),
        "admins": stats.get(UserRoleEnum.ADMIN, 0),
    }
