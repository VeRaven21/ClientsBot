from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from database.models import User
from core.db import SessionLocal
from services import client_service

router = Router()


@router.callback_query(F.data == "client.my_orders")
async def my_orders(callback_query: CallbackQuery):
    """Обработчик просмотра заказов клиента"""
    client_tg_id = callback_query.from_user.id

    async with SessionLocal() as session:
        # Получаем ID клиента
        result = await session.execute(
            select(User.id).where(User.tg_id == client_tg_id)
        )
        client_id = result.scalar_one_or_none()

        if not client_id:
            await callback_query.answer(
                "Ошибка: пользователь не найден", show_alert=True
            )
            return

        # Получаем активные заказы клиента
        orders = await client_service.get_client_active_orders(session, str(client_id))

    # Форматируем текст с заказами
    text = client_service.format_client_orders_text(orders)

    # Добавляем кнопку "Назад"
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="↩️ Назад", callback_data="client.main_menu"))

    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())
    await callback_query.answer()
