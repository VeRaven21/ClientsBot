from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List, Tuple
import crud.orders_crud as orders_crud
from database.models import Order, User, Service


async def get_worker_orders_by_date(
    session: AsyncSession, worker_id: str, date: datetime
) -> List[Tuple[Order, User, Service]]:
    """Получить заказы сотрудника на конкретную дату"""
    return await orders_crud.get_orders_by_worker_and_date(session, worker_id, date)


def format_orders_text(
    orders: List[Tuple[Order, User, Service]], date: datetime
) -> str:
    """Форматировать текст с заказами для отображения"""
    # Форматируем дату для отображения
    date_formatted = date.strftime("%d.%m.%Y")
    day_name = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье",
    ][date.weekday()]

    # Определяем, сегодня ли это
    today = datetime.now().date()
    if date.date() == today:
        date_title = f"📅 Сегодня ({date_formatted}, {day_name})"
    elif date.date() == today + timedelta(days=1):
        date_title = f"📅 Завтра ({date_formatted}, {day_name})"
    elif date.date() == today - timedelta(days=1):
        date_title = f"📅 Вчера ({date_formatted}, {day_name})"
    else:
        date_title = f"📅 {date_formatted} ({day_name})"

    if not orders:
        return f"{date_title}\n\n❌ На этот день заказов нет."

    text = f"{date_title}\n\n📋 <b>Заказы ({len(orders)}):</b>\n\n"

    for order, client, service in orders:
        time_str = order.start_time.strftime("%H:%M")

        # Формируем информацию о клиенте
        client_info = f"👤 Клиент: {client.name}"
        if client.username:
            client_info += f" (@{client.username})"

        text += (
            f"🕐 <b>{time_str}</b>\n"
            f"💼 Услуга: {service.name}\n"
            f"💰 Цена: {service.price} руб.\n"
            f"⏱ Длительность: {service.lenght} мин.\n"
            f"{client_info}\n"
            f"{'─' * 30}\n\n"
        )

    return text
