from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


async def admin_menu() -> InlineKeyboardBuilder:
    """Создает клавиатуру главного меню админа"""
    kb = InlineKeyboardBuilder()
    kb.button(text="Управление пользователями", callback_data="admin.users_management")
    kb.button(text="Управление услугами", callback_data="admin.services_management")
    kb.button(text="Управление заказами", callback_data="admin.orders_management")
    kb.button(text="Управление сотрудниками", callback_data="admin.workers_management")
    kb.adjust(2)
    return kb


@router.callback_query(F.data == "admin.main_menu")
async def main_menu(callback_query: CallbackQuery):
    """Обработчик главного меню админа"""
    kb = await admin_menu()
    text = "Выберите действие:"
    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())
