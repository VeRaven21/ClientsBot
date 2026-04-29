from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data == "client.my_orders")
async def my_orders(callback_query: CallbackQuery):
    """Обработчик просмотра заказов клиента (заглушка)"""
    await callback_query.answer("Функция в разработке", show_alert=True)
