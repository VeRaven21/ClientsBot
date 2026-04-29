from datetime import datetime, timedelta
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from database.models import Order, User, Service
from aiogram import Bot


async def get_orders_for_reminder(
    session: AsyncSession, hours_before: int = 2
) -> List[Tuple[Order, User, Service]]:
    """
    Получить заказы, для которых нужно отправить напоминание
    Возвращает заказы, которые начнутся через указанное количество часов
    """
    now = datetime.now()
    reminder_time_start = now + timedelta(hours=hours_before, minutes=-5)
    reminder_time_end = now + timedelta(hours=hours_before, minutes=5)

    result = await session.execute(
        select(Order, User, Service)
        .join(User, Order.client_id == User.id)
        .join(Service, Order.service_id == Service.id)
        .where(
            and_(
                Order.start_time >= reminder_time_start,
                Order.start_time <= reminder_time_end,
            )
        )
    )
    return result.all()


def format_reminder_message(
    service_name: str, start_time: datetime, duration: int, worker_name: str
) -> str:
    """Форматировать сообщение-напоминание о заказе"""
    time_str = start_time.strftime("%d.%m.%Y %H:%M")
    end_time = start_time + timedelta(minutes=duration)
    end_time_str = end_time.strftime("%H:%M")

    return (
        f"🔔 <b>Напоминание о заказе!</b>\n\n"
        f"Ваш заказ через 2 часа:\n\n"
        f"💼 Услуга: {service_name}\n"
        f"👷 Мастер: {worker_name}\n"
        f"🕐 Время: {time_str} - {end_time_str}\n"
        f"⏱ Длительность: {duration} мин.\n\n"
        f"Не забудьте прийти вовремя!"
    )


async def send_reminders(bot: Bot, session: AsyncSession) -> int:
    """
    Отправить напоминания клиентам о предстоящих заказах
    Возвращает количество отправленных напоминаний
    """
    orders = await get_orders_for_reminder(session, hours_before=2)
    sent_count = 0

    for order, client, service in orders:
        # Получаем данные мастера
        worker = await session.get(User, order.worker_id)
        if not worker:
            continue

        # Форматируем сообщение
        message = format_reminder_message(
            service.name, order.start_time, service.lenght, worker.name
        )

        # Отправляем напоминание клиенту
        try:
            await bot.send_message(client.tg_id, message)
            sent_count += 1
        except Exception:
            # Если не удалось отправить, пропускаем
            continue

    return sent_count
