from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data == "worker.services_management")
async def services_management(callback_query: CallbackQuery):
    """Обработчик управления услугами работника (заглушка)"""
    await callback_query.answer("Функция в разработке", show_alert=True)
