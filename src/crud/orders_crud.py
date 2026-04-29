from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta
from database.models import Order, User, Service
from typing import List, Tuple


async def get_orders_by_worker_and_date(
    session: AsyncSession, worker_id: str, date: datetime
) -> List[Tuple[Order, User, Service]]:
    """Получить заказы сотрудника на конкретную дату"""
    # Начало и конец дня
    start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    # Получаем заказы на этот день
    result = await session.execute(
        select(Order, User, Service)
        .join(User, Order.client_id == User.id)
        .join(Service, Order.service_id == Service.id)
        .where(
            and_(
                Order.worker_id == worker_id,
                Order.start_time >= start_of_day,
                Order.start_time < end_of_day,
            )
        )
        .order_by(Order.start_time)
    )
    return result.all()


async def get_total_orders_count(session: AsyncSession) -> int:
    """Получить общее количество заказов"""
    result = await session.execute(select(func.count(Order.id)))
    return result.scalar()
