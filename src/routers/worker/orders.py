from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from datetime import datetime, timedelta
from database.models import User
from core.db import SessionLocal
from services import orders_service

router = Router()


async def create_date_navigation(
    current_date: datetime, worker_id: str
) -> InlineKeyboardBuilder:
    """Создает навигацию по датам"""
    kb = InlineKeyboardBuilder()

    # Форматируем даты для callback_data
    prev_date = (current_date - timedelta(days=1)).strftime("%Y-%m-%d")
    next_date = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")

    # Кнопки навигации
    kb.row(
        InlineKeyboardButton(
            text="◀️ Предыдущий день", callback_data=f"worker.orders_date|{prev_date}"
        ),
        InlineKeyboardButton(
            text="Следующий день ▶️", callback_data=f"worker.orders_date|{next_date}"
        ),
    )

    # Кнопка "Сегодня"
    today = datetime.now().strftime("%Y-%m-%d")
    kb.row(
        InlineKeyboardButton(
            text="📅 Сегодня", callback_data=f"worker.orders_date|{today}"
        )
    )

    # Кнопка "Назад"
    kb.row(InlineKeyboardButton(text="↩️ Назад", callback_data="worker.main_menu"))

    return kb


@router.callback_query(F.data == "worker.my_orders")
async def my_orders(callback_query: CallbackQuery):
    """Обработчик просмотра заказов работника - показывает заказы на сегодня"""
    worker_tg_id = callback_query.from_user.id

    async with SessionLocal() as session:
        # Получаем ID работника
        result = await session.execute(
            select(User.id).where(User.tg_id == worker_tg_id)
        )
        worker_id = result.scalar_one_or_none()

        if not worker_id:
            await callback_query.answer(
                "Ошибка: пользователь не найден", show_alert=True
            )
            return

    # Показываем заказы на сегодня
    today = datetime.now()
    await show_orders_for_date(callback_query, worker_id, today)


@router.callback_query(F.data.startswith("worker.orders_date|"))
async def orders_by_date(callback_query: CallbackQuery):
    """Обработчик просмотра заказов на конкретную дату"""
    worker_tg_id = callback_query.from_user.id
    date_str = callback_query.data.split("|")[1]

    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        await callback_query.answer("Ошибка: неверный формат даты", show_alert=True)
        return

    async with SessionLocal() as session:
        # Получаем ID работника
        result = await session.execute(
            select(User.id).where(User.tg_id == worker_tg_id)
        )
        worker_id = result.scalar_one_or_none()

        if not worker_id:
            await callback_query.answer(
                "Ошибка: пользователь не найден", show_alert=True
            )
            return

    await show_orders_for_date(callback_query, worker_id, selected_date)


async def show_orders_for_date(
    callback_query: CallbackQuery, worker_id: str, date: datetime
):
    """Показать заказы на конкретную дату"""
    async with SessionLocal() as session:
        orders = await orders_service.get_worker_orders_by_date(
            session, worker_id, date
        )

    text = orders_service.format_orders_text(orders, date)
    kb = await create_date_navigation(date, worker_id)
    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())
