from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data == "worker.my_orders")
async def my_orders(callback_query: CallbackQuery):
    """Обработчик просмотра заказов работника (заглушка)"""
    await callback_query.answer("Функция в разработке", show_alert=True)
