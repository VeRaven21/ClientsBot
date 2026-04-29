from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


async def worker_menu() -> InlineKeyboardBuilder:
    """Создает клавиатуру главного меню работника"""
    kb = InlineKeyboardBuilder()
    kb.button(text="Мои заказы", callback_data="worker.my_orders")
    kb.adjust(1)
    return kb


@router.callback_query(F.data == "worker.main_menu")
async def main_menu(callback_query: CallbackQuery):
    """Обработчик главного меню работника"""
    text = "Выберите действие:"
    kb = await worker_menu()
    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())
