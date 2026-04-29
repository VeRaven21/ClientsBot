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


async def get_active_client_orders(
    session: AsyncSession, client_id: str
) -> List[Tuple[Order, User, Service]]:
    """Получить активные (будущие) заказы клиента"""
    now = datetime.now()
    # Убираем timezone если есть
    if now.tzinfo is not None:
        now = now.replace(tzinfo=None)

    result = await session.execute(
        select(Order, User, Service)
        .join(User, Order.worker_id == User.id)
        .join(Service, Order.service_id == Service.id)
        .where(Order.client_id == client_id, Order.start_time >= now)
        .order_by(Order.start_time)
    )
    return result.all()


async def get_worker_orders_at_time(
    session: AsyncSession, worker_id: str, start_time: datetime, duration_minutes: int
) -> List[Tuple[Order, Service]]:
    """
    Получить заказы сотрудника, которые пересекаются с указанным временем
    Проверяет, занят ли сотрудник в указанное время
    """
    # Убираем timezone из start_time если есть
    if start_time.tzinfo is not None:
        start_time = start_time.replace(tzinfo=None)

    end_time = start_time + timedelta(minutes=duration_minutes)

    # Получаем все заказы сотрудника с информацией об услугах
    result = await session.execute(
        select(Order, Service)
        .join(Service, Order.service_id == Service.id)
        .where(Order.worker_id == worker_id)
    )
    orders_with_services = result.all()

    # Фильтруем заказы, которые пересекаются с указанным временем
    conflicting_orders = []
    for order, service in orders_with_services:
        # Убираем timezone из order.start_time если есть
        order_start = order.start_time
        if order_start.tzinfo is not None:
            order_start = order_start.replace(tzinfo=None)

        order_end_time = order_start + timedelta(minutes=service.lenght)

        # Проверяем пересечение интервалов
        if order_start < end_time and order_end_time > start_time:
            conflicting_orders.append((order, service))

    return conflicting_orders


async def create_order(
    session: AsyncSession,
    client_id: str,
    worker_id: str,
    service_id: str,
    start_time: datetime,
) -> Order:
    """Создать новый заказ"""
    order = Order(
        client_id=client_id,
        worker_id=worker_id,
        service_id=service_id,
        start_time=start_time,
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def delete_client_orders(session: AsyncSession, client_id: str) -> None:
    """Удалить все заказы клиента"""
    result = await session.execute(select(Order).where(Order.client_id == client_id))
    orders = result.scalars().all()
    for order in orders:
        await session.delete(order)
    await session.commit()
