import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder


from routers import admin, client, worker

import services.user_service as user_service

from database.models import User, UserRoleEnum

from core.db import SessionLocal
from core.config import settings


dp = Dispatcher()
dp.include_router(admin.router)
dp.include_router(client.router)
dp.include_router(worker.router)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with SessionLocal() as session:
        user: User | None = await user_service.get_user_by_tg_id(
            message.from_user.id, session
        )

        kb = InlineKeyboardBuilder()

        if not user:
            # Определяем роль нового пользователя
            admin_ids = settings.get_admin_ids()
            role = (
                UserRoleEnum.ADMIN
                if message.from_user.id in admin_ids
                else UserRoleEnum.CLIENT
            )

            user = User(
                tg_id=message.from_user.id,
                name=message.from_user.first_name,
                username=message.from_user.username,
                role=role,
            )
            await user_service.add_user_to_db(user, session)

        if user.role == UserRoleEnum.WORKER:
            kb.button(text="Мои заказы", callback_data="worker.my_orders")
            text = f"Приветствую, {message.from_user.first_name}! Выберите действие:"
        elif user.role == UserRoleEnum.ADMIN:
            kb.button(
                text="Управление пользователями", callback_data="admin.users_management"
            )
            kb.button(
                text="Управление услугами", callback_data="admin.services_management"
            )
            kb.button(
                text="Управление заказами", callback_data="admin.orders_management"
            )
            kb.button(
                text="Управление сотрудниками", callback_data="admin.workers_management"
            )
            kb.adjust(2)
            text = f"Приветствую, {message.from_user.first_name}! Выберите действие:"
        else:
            kb.button(text="Заказать услугу", callback_data="client.new_order")
            kb.button(text="Мои заказы", callback_data="client.my_orders")
            kb.button(text="Удалить аккаунт", callback_data="client.delete_account")
            text = f"{message.from_user.first_name}, добро пожаловать в систему заказа услуг! Выберите действие:"

    await message.answer(text, reply_markup=kb.as_markup())


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
