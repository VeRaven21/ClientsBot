from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func
from database.models import User, UserRoleEnum
from core.db import SessionLocal

router = Router()


@router.callback_query(F.data == "admin.users_management")
async def users_management(callback_query: CallbackQuery):
    """Обработчик управления пользователями - показывает статистику"""
    async with SessionLocal() as session:
        # Получаем количество пользователей по ролям
        result = await session.execute(
            select(User.role, func.count(User.id)).group_by(User.role)
        )
        stats = dict(result.all())

        # Получаем общее количество
        total_result = await session.execute(select(func.count(User.id)))
        total = total_result.scalar()

    # Формируем текст статистики
    clients = stats.get(UserRoleEnum.CLIENT, 0)
    workers = stats.get(UserRoleEnum.WORKER, 0)
    admins = stats.get(UserRoleEnum.ADMIN, 0)

    text = (
        f"📊 <b>Статистика пользователей</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n\n"
        f"👤 Клиентов: <b>{clients}</b>\n"
        f"👷 Работников: <b>{workers}</b>\n"
        f"👨‍💼 Администраторов: <b>{admins}</b>"
    )

    # Добавляем кнопку "Назад"
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Назад", callback_data="admin.main_menu"))

    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())
    await callback_query.answer()
