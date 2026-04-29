from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


async def client_menu() -> InlineKeyboardBuilder:
    """Создает клавиатуру главного меню клиента"""
    kb = InlineKeyboardBuilder()
    kb.button(text="Заказать услугу", callback_data="client.new_order")
    kb.button(text="Мои заказы", callback_data="client.my_orders")
    kb.adjust(1)
    return kb


@router.callback_query(F.data == "client.main_menu")
async def main_menu(callback_query: CallbackQuery):
    """Обработчик главного меню клиента"""
    text = "Выберите действие:"
    kb = await client_menu()
    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())
