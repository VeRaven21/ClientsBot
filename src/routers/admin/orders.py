from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func
from database.models import Order
from core.db import SessionLocal

router = Router()


@router.callback_query(F.data == "admin.orders_management")
async def orders_management(callback_query: CallbackQuery):
    """Обработчик управления заказами - показывает количество заказов"""
    async with SessionLocal() as session:
        # Получаем общее количество заказов
        result = await session.execute(select(func.count(Order.id)))
        total_orders = result.scalar()

    text = (
        f"📋 <b>Управление заказами</b>\n\n"
        f"Всего заказов в системе: <b>{total_orders}</b>"
    )

    # Добавляем кнопку "Назад"
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Назад", callback_data="admin.main_menu"))

    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())
    await callback_query.answer()
