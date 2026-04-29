from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from sqlalchemy import select, func
from database.models import User, UserRoleEnum, Order
from core.db import SessionLocal

router = Router()


class AddWorkerState(StatesGroup):
    """Состояния для добавления сотрудника"""

    contact = State()


async def workers_list_page(page: int, button_prefix: str) -> InlineKeyboardBuilder:
    """Создает клавиатуру со списком сотрудников с пагинацией"""
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.role == UserRoleEnum.WORKER).order_by(User.name)
        )
        workers = result.scalars().all()

    kb = InlineKeyboardBuilder()
    total_workers = len(workers)
    total_pages = (
        total_workers + 4
    ) // 5  # Округление вверх для 5 сотрудников на страницу

    # Проверяем, что страница в допустимых пределах
    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages

    start = (page - 1) * 5
    end = start + 5

    # Добавляем кнопки сотрудников по одной в строке
    for worker in workers[start:end]:
        kb.row(
            InlineKeyboardButton(
                text=f"{worker.name}",
                callback_data=f"{button_prefix}|{worker.id}",
            )
        )

    # Добавляем кнопки управления
    nav_buttons = []

    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⏪", callback_data=f"{button_prefix}|prev|{page}"
            )
        )
    else:
        nav_buttons.append(
            InlineKeyboardButton(text="⏪", callback_data=f"{button_prefix}|noop")
        )

    nav_buttons.append(
        InlineKeyboardButton(text="↩️", callback_data=f"{button_prefix}|back")
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⏩", callback_data=f"{button_prefix}|next|{page}"
            )
        )
    else:
        nav_buttons.append(
            InlineKeyboardButton(text="⏩", callback_data=f"{button_prefix}|noop")
        )

    kb.row(*nav_buttons)

    return kb


async def workers_management_menu() -> InlineKeyboardBuilder:
    """Создает клавиатуру меню управления сотрудниками"""
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text="Список сотрудников", callback_data="admin.workers_list"
        )
    )
    kb.row(
        InlineKeyboardButton(
            text="Добавить сотрудника", callback_data="admin.add_worker"
        )
    )
    kb.row(InlineKeyboardButton(text="Назад", callback_data="admin.main_menu"))
    return kb


@router.callback_query(F.data == "admin.workers_management")
async def workers_management(callback_query: CallbackQuery):
    """Обработчик управления сотрудниками"""
    async with SessionLocal() as session:
        result = await session.execute(
            select(func.count(User.id)).where(User.role == UserRoleEnum.WORKER)
        )
        workers_count = result.scalar()

    kb = await workers_management_menu()
    text = f"👷 <b>Управление сотрудниками</b>\n\nВсего сотрудников: <b>{workers_count}</b>\n\nВыберите действие:"
    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "admin.workers_list")
async def workers_list(callback_query: CallbackQuery):
    """Показать список сотрудников"""
    kb = await workers_list_page(1, "admin.worker_select")
    await callback_query.message.edit_text(
        "Выберите сотрудника:", reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.startswith("admin.worker_select|"))
async def worker_select_action(callback_query: CallbackQuery):
    """Обработка выбора сотрудника"""
    parts = callback_query.data.split("|")

    # Обработка noop (неактивные кнопки)
    if len(parts) >= 2 and parts[1] == "noop":
        await callback_query.answer()
        return

    # Обработка выбора сотрудника
    if len(parts) >= 2 and parts[1] not in ("back", "prev", "next", "noop"):
        worker_id = parts[1]

        async with SessionLocal() as session:
            worker = await session.get(User, worker_id)
            if not worker or worker.role != UserRoleEnum.WORKER:
                await callback_query.answer("Сотрудник не найден", show_alert=True)
                return

            # Получаем количество заказов сотрудника
            orders_result = await session.execute(
                select(func.count(Order.id)).where(Order.worker_id == worker.id)
            )
            orders_count = orders_result.scalar()

        # Показываем меню управления сотрудником
        kb = InlineKeyboardBuilder()
        kb.row(
            InlineKeyboardButton(
                text="Просмотр заказов",
                callback_data=f"admin.worker_orders|{worker_id}",
            )
        )
        kb.row(
            InlineKeyboardButton(
                text="Удалить сотрудника",
                callback_data=f"admin.worker_delete|{worker_id}",
            )
        )
        kb.row(InlineKeyboardButton(text="Назад", callback_data="admin.workers_list"))

        text = (
            f"👷 <b>Сотрудник: {worker.name}</b>\n\n"
            f"ID: <code>{worker.tg_id}</code>\n"
            f"Заказов: <b>{orders_count}</b>\n\n"
            f"Выберите действие:"
        )

        await callback_query.message.edit_text(text, reply_markup=kb.as_markup())

    # Обработка кнопки "назад"
    elif len(parts) >= 2 and parts[1] == "back":
        await workers_management(callback_query)

    # Обработка пагинации
    elif len(parts) >= 2 and parts[1] in ("prev", "next"):
        try:
            page = int(parts[2])
        except IndexError, ValueError:
            page = 1
        if parts[1] == "prev":
            page = max(1, page - 1)
        else:
            page = page + 1
        kb = await workers_list_page(page, "admin.worker_select")
        await callback_query.message.edit_text(
            "Выберите сотрудника:", reply_markup=kb.as_markup()
        )


@router.callback_query(F.data.startswith("admin.worker_orders|"))
async def worker_orders(callback_query: CallbackQuery):
    """Просмотр заказов сотрудника"""
    worker_id = callback_query.data.split("|")[1]

    async with SessionLocal() as session:
        worker = await session.get(User, worker_id)
        if not worker:
            await callback_query.answer("Сотрудник не найден", show_alert=True)
            return

        # Получаем заказы сотрудника
        orders_result = await session.execute(
            select(Order)
            .where(Order.worker_id == worker.id)
            .order_by(Order.start_time.desc())
        )
        orders = orders_result.scalars().all()

    if not orders:
        text = f"👷 <b>{worker.name}</b>\n\nУ сотрудника пока нет заказов."
    else:
        text = f"👷 <b>{worker.name}</b>\n\n📋 <b>Заказы ({len(orders)}):</b>\n\n"
        for order in orders[:10]:  # Показываем первые 10 заказов
            text += f"• Заказ от {order.start_time.strftime('%d.%m.%Y %H:%M')}\n"

    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text="Назад", callback_data=f"admin.worker_select|{worker_id}"
        )
    )

    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("admin.worker_delete|"))
async def worker_delete(callback_query: CallbackQuery):
    """Удаление сотрудника (смена роли на CLIENT)"""
    worker_id = callback_query.data.split("|")[1]

    async with SessionLocal() as session:
        worker = await session.get(User, worker_id)
        if not worker or worker.role != UserRoleEnum.WORKER:
            await callback_query.answer("Сотрудник не найден", show_alert=True)
            return

        # Меняем роль на CLIENT
        worker.role = UserRoleEnum.CLIENT
        await session.commit()

    await callback_query.answer(
        f"Сотрудник {worker.name} удален из списка сотрудников", show_alert=True
    )

    # Возвращаемся к списку сотрудников
    kb = await workers_list_page(1, "admin.worker_select")
    await callback_query.message.edit_text(
        "Выберите сотрудника:", reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "admin.add_worker")
async def add_worker(callback_query: CallbackQuery, state: FSMContext):
    """Начало процесса добавления сотрудника"""
    await state.set_state(AddWorkerState.contact)

    # Создаем клавиатуру с кнопкой "Отмена"
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
    )

    await callback_query.message.answer(
        "Отправьте контакт пользователя или его username (@username), которого хотите сделать сотрудником.\n\n"
        "Для отправки контакта: нажмите на скрепку → Контакт → выберите пользователя.\n"
        "Для отправки username: просто напишите @username",
        reply_markup=cancel_kb,
    )
    await callback_query.answer()


@router.message(F.text == "Отмена", StateFilter(AddWorkerState))
async def cancel_add_worker(message: Message, state: FSMContext):
    """Отмена добавления сотрудника"""
    await state.clear()
    await message.answer(
        "Добавление сотрудника отменено.", reply_markup=ReplyKeyboardRemove()
    )

    async with SessionLocal() as session:
        result = await session.execute(
            select(func.count(User.id)).where(User.role == UserRoleEnum.WORKER)
        )
        workers_count = result.scalar()

    kb = await workers_management_menu()
    text = f"👷 <b>Управление сотрудниками</b>\n\nВсего сотрудников: <b>{workers_count}</b>\n\nВыберите действие:"
    await message.answer(text, reply_markup=kb.as_markup())


@router.message(AddWorkerState.contact, F.contact)
async def process_worker_contact(message: Message, state: FSMContext):
    """Обработка контакта для добавления сотрудника"""
    contact = message.contact
    user_id = contact.user_id

    if not user_id:
        cancel_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
        )
        await message.answer(
            "Не удалось получить ID пользователя из контакта. Попробуйте еще раз.",
            reply_markup=cancel_kb,
        )
        return

    await add_user_as_worker(message, state, user_id, contact.first_name)


@router.message(AddWorkerState.contact, F.text)
async def process_worker_username(message: Message, state: FSMContext):
    """Обработка username для добавления сотрудника"""
    text = message.text.strip()

    # Проверяем, что это username (начинается с @)
    if not text.startswith("@"):
        cancel_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
        )
        await message.answer(
            "Username должен начинаться с @. Попробуйте еще раз или отправьте контакт.",
            reply_markup=cancel_kb,
        )
        return

    username = text[1:]  # Убираем @

    # Ищем пользователя по username в базе данных
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(
                f"⚠️ Пользователь @{username} не найден в базе данных.\n\n"
                f"Попросите пользователя @{username} запустить бота командой /start, "
                f"а затем попробуйте снова.",
                reply_markup=ReplyKeyboardRemove(),
            )

            await state.clear()

            result = await session.execute(
                select(func.count(User.id)).where(User.role == UserRoleEnum.WORKER)
            )
            workers_count = result.scalar()

            kb = await workers_management_menu()
            text = f"👷 <b>Управление сотрудниками</b>\n\nВсего сотрудников: <b>{workers_count}</b>\n\nВыберите действие:"
            await message.answer(text, reply_markup=kb.as_markup())
        else:
            # Пользователь найден, добавляем его как сотрудника
            await add_user_as_worker(message, state, user.tg_id, user.name)


async def add_user_as_worker(
    message: Message, state: FSMContext, user_id: int, user_name: str
):
    """Общая функция для добавления пользователя как сотрудника"""
    async with SessionLocal() as session:
        # Ищем пользователя в базе
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer(
                f"Пользователь {user_name} не найден в базе данных.\n"
                f"Он должен сначала запустить бота командой /start",
                reply_markup=ReplyKeyboardRemove(),
            )
        elif user.role == UserRoleEnum.WORKER:
            await message.answer(
                f"{user.name} уже является сотрудником.",
                reply_markup=ReplyKeyboardRemove(),
            )
        elif user.role == UserRoleEnum.ADMIN:
            await message.answer(
                f"{user.name} является администратором.",
                reply_markup=ReplyKeyboardRemove(),
            )
        else:
            # Меняем роль на WORKER
            user.role = UserRoleEnum.WORKER
            await session.commit()

            await message.answer(
                f"✅ {user.name} успешно добавлен в список сотрудников!",
                reply_markup=ReplyKeyboardRemove(),
            )

    await state.clear()

    async with SessionLocal() as session:
        result = await session.execute(
            select(func.count(User.id)).where(User.role == UserRoleEnum.WORKER)
        )
        workers_count = result.scalar()

    kb = await workers_management_menu()
    text = f"👷 <b>Управление сотрудниками</b>\n\nВсего сотрудников: <b>{workers_count}</b>\n\nВыберите действие:"
    await message.answer(text, reply_markup=kb.as_markup())


@router.message(AddWorkerState.contact)
async def process_invalid_contact(message: Message):
    """Обработка неправильного ввода при добавлении сотрудника"""
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
    )
    await message.answer(
        "Пожалуйста, отправьте контакт пользователя или его username (@username).\n\n"
        "Для отправки контакта: нажмите на скрепку → Контакт → выберите пользователя.\n"
        "Для отправки username: просто напишите @username",
        reply_markup=cancel_kb,
    )
