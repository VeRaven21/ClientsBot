from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List, Tuple
from database.models import Order, User, Service
from core.config import settings
import crud.orders_crud as orders_crud
import crud.user_crud as user_crud
import crud.workers_crud as workers_crud


async def get_client_active_orders(
    session: AsyncSession, client_id: str
) -> List[Tuple[Order, User, Service]]:
    """Получить активные заказы клиента"""
    return await orders_crud.get_active_client_orders(session, client_id)


def format_client_orders_text(orders: List[Tuple[Order, User, Service]]) -> str:
    """Форматировать текст с заказами клиента"""
    if not orders:
        return "У вас пока нет активных заказов."

    text = f"📋 <b>Ваши заказы ({len(orders)}):</b>\n\n"

    for order, worker, service in orders:
        time_str = order.start_time.strftime("%d.%m.%Y %H:%M")
        end_time = order.start_time + timedelta(minutes=service.lenght)
        end_time_str = end_time.strftime("%H:%M")

        text += (
            f"🕐 <b>{time_str} - {end_time_str}</b>\n"
            f"💼 Услуга: {service.name}\n"
            f"💰 Цена: {service.price} руб.\n"
            f"⏱ Длительность: {service.lenght} мин.\n"
            f"👷 Мастер: {worker.name}\n"
            f"{'─' * 30}\n\n"
        )

    return text


async def get_available_workers_at_time(
    session: AsyncSession, start_time: datetime, duration_minutes: int
) -> List[User]:
    """
    Получить список свободных сотрудников на указанное время
    Сотрудник считается свободным, если у него нет заказов, которые пересекаются с указанным временем
    """
    # Получаем всех сотрудников
    all_workers = await workers_crud.get_workers_list(session)

    available_workers = []
    for worker in all_workers:
        # Проверяем, есть ли у сотрудника заказы в это время
        conflicting_orders = await orders_crud.get_worker_orders_at_time(
            session, str(worker.id), start_time, duration_minutes
        )

        # Если нет пересекающихся заказов, сотрудник свободен
        if not conflicting_orders:
            available_workers.append(worker)

    return available_workers


async def create_client_order(
    session: AsyncSession,
    client_id: str,
    worker_id: str,
    service_id: str,
    start_time: datetime,
) -> Order:
    """Создать заказ для клиента"""
    return await orders_crud.create_order(
        session, client_id, worker_id, service_id, start_time
    )


async def delete_client_account(session: AsyncSession, client_id: str) -> bool:
    """
    Удалить аккаунт клиента и все его заказы
    Возвращает True если успешно удалено
    """
    # Сначала удаляем все заказы клиента
    await orders_crud.delete_client_orders(session, client_id)

    # Затем удаляем самого клиента
    return await user_crud.delete_user(session, client_id)


def generate_time_slots(date: datetime, step_minutes: int = None) -> List[datetime]:
    """
    Генерировать временные слоты на день с указанным шагом
    Рабочее время берется из настроек
    """
    if step_minutes is None:
        step_minutes = settings.BOOKING_INTERVAL_MINUTES

    slots = []
    start_hour = settings.WORK_START_HOUR
    end_hour = settings.WORK_END_HOUR

    current = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)

    while current < end:
        slots.append(current)
        current += timedelta(minutes=step_minutes)

    return slots


def format_order_notification(
    client_name: str, service_name: str, start_time: datetime, duration: int
) -> str:
    """Форматировать уведомление о новом заказе для мастера"""
    time_str = start_time.strftime("%d.%m.%Y %H:%M")
    end_time = start_time + timedelta(minutes=duration)
    end_time_str = end_time.strftime("%H:%M")

    return (
        f"🔔 <b>Новый заказ!</b>\n\n"
        f"👤 Клиент: {client_name}\n"
        f"💼 Услуга: {service_name}\n"
        f"🕐 Время: {time_str} - {end_time_str}\n"
        f"⏱ Длительность: {duration} мин."
    )


def format_order_confirmation(
    worker_name: str, service_name: str, start_time: datetime, duration: int, price: int
) -> str:
    """Форматировать подтверждение заказа для клиента"""
    time_str = start_time.strftime("%d.%m.%Y %H:%M")
    end_time = start_time + timedelta(minutes=duration)
    end_time_str = end_time.strftime("%H:%M")

    return (
        f"✅ <b>Заказ успешно создан!</b>\n\n"
        f"💼 Услуга: {service_name}\n"
        f"👷 Мастер: {worker_name}\n"
        f"🕐 Время: {time_str} - {end_time_str}\n"
        f"⏱ Длительность: {duration} мин.\n"
        f"💰 Цена: {price} руб."
    )
