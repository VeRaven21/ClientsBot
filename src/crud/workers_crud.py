from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User, UserRoleEnum, Order
from typing import List


async def get_workers_list(session: AsyncSession) -> List[User]:
    """Получить список всех сотрудников"""
    result = await session.execute(
        select(User).where(User.role == UserRoleEnum.WORKER).order_by(User.name)
    )
    return result.scalars().all()


async def get_workers_count(session: AsyncSession) -> int:
    """Получить количество сотрудников"""
    result = await session.execute(
        select(func.count(User.id)).where(User.role == UserRoleEnum.WORKER)
    )
    return result.scalar()


async def get_worker_by_id(session: AsyncSession, worker_id: str) -> User | None:
    """Получить сотрудника по ID"""
    return await session.get(User, worker_id)


async def get_worker_orders_count(session: AsyncSession, worker_id: str) -> int:
    """Получить количество заказов сотрудника"""
    result = await session.execute(
        select(func.count(Order.id)).where(Order.worker_id == worker_id)
    )
    return result.scalar()


async def get_worker_recent_orders(
    session: AsyncSession, worker_id: str, limit: int = 10
) -> List[Order]:
    """Получить последние заказы сотрудника"""
    result = await session.execute(
        select(Order)
        .where(Order.worker_id == worker_id)
        .order_by(Order.start_time.desc())
        .limit(limit)
    )
    return result.scalars().all()


async def change_user_role(
    session: AsyncSession, user_id: str, new_role: UserRoleEnum
) -> bool:
    """Изменить роль пользователя"""
    user = await session.get(User, user_id)
    if not user:
        return False
    user.role = new_role
    await session.commit()
    return True


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    """Получить пользователя по username"""
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()
