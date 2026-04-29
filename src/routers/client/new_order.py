from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data == "client.new_order")
async def new_order(callback_query: CallbackQuery):
    """Обработчик создания нового заказа (заглушка)"""
    await callback_query.answer("Функция в разработке", show_alert=True)
