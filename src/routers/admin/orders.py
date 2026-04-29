from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.db import SessionLocal
from crud import orders_crud

router = Router()


@router.callback_query(F.data == "admin.orders_management")
async def orders_management(callback_query: CallbackQuery):
    """Обработчик управления заказами - показывает количество заказов"""
    async with SessionLocal() as session:
        total_orders = await orders_crud.get_total_orders_count(session)

    text = (
        f"📋 <b>Управление заказами</b>\n\n"
        f"Всего заказов в системе: <b>{total_orders}</b>"
    )

    # Добавляем кнопку "Назад"
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Назад", callback_data="admin.main_menu"))

    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())
    await callback_query.answer()
