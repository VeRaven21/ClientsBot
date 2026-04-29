from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from database.models import User
from core.db import SessionLocal
from services import client_service

router = Router()


async def client_menu() -> InlineKeyboardBuilder:
    """Создает клавиатуру главного меню клиента"""
    kb = InlineKeyboardBuilder()
    kb.button(text="Заказать услугу", callback_data="client.new_order")
    kb.button(text="Мои заказы", callback_data="client.my_orders")
    kb.button(text="Удалить аккаунт", callback_data="client.delete_account")
    kb.adjust(1)
    return kb


@router.callback_query(F.data == "client.main_menu")
async def main_menu(callback_query: CallbackQuery):
    """Обработчик главного меню клиента"""
    text = "Выберите действие:"
    kb = await client_menu()
    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "client.delete_account")
async def delete_account_confirm(callback_query: CallbackQuery):
    """Подтверждение удаления аккаунта"""
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text="✅ Да, удалить", callback_data="client.delete_account_confirm"
        )
    )
    kb.row(InlineKeyboardButton(text="❌ Отмена", callback_data="client.main_menu"))

    text = (
        "⚠️ <b>Внимание!</b>\n\n"
        "Вы уверены, что хотите удалить свой аккаунт?\n"
        "Все ваши данные и заказы будут безвозвратно удалены."
    )

    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "client.delete_account_confirm")
async def delete_account_execute(callback_query: CallbackQuery):
    """Выполнение удаления аккаунта"""
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

        # Удаляем аккаунт клиента
        success = await client_service.delete_client_account(session, str(client_id))

    if success:
        await callback_query.message.edit_text(
            "✅ Ваш аккаунт успешно удален.\n\n"
            "Для повторного использования бота отправьте команду /start"
        )
    else:
        await callback_query.answer("Ошибка при удалении аккаунта", show_alert=True)
