from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.db import SessionLocal
from crud import user_crud

router = Router()


@router.callback_query(F.data == "admin.users_management")
async def users_management(callback_query: CallbackQuery):
    """Обработчик управления пользователями - показывает статистику"""
    async with SessionLocal() as session:
        stats = await user_crud.get_users_stats(session)

    text = (
        f"📊 <b>Статистика пользователей</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total']}</b>\n\n"
        f"👤 Клиентов: <b>{stats['clients']}</b>\n"
        f"👷 Работников: <b>{stats['workers']}</b>\n"
        f"👨‍💼 Администраторов: <b>{stats['admins']}</b>"
    )

    # Добавляем кнопку "Назад"
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Назад", callback_data="admin.main_menu"))

    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())
    await callback_query.answer()
