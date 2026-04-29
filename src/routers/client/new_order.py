from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from datetime import datetime, timedelta
from database.models import User
from core.db import SessionLocal
from services import client_service, services_service

router = Router()


class NewOrderState(StatesGroup):
    """Состояния для создания нового заказа"""

    service = State()
    date = State()
    time = State()
    worker = State()


@router.callback_query(F.data == "client.new_order")
async def new_order_start(callback_query: CallbackQuery, state: FSMContext):
    """Начало процесса создания заказа - выбор услуги"""
    await state.set_state(NewOrderState.service)
    await show_services_page(callback_query, state, page=1)


async def show_services_page(
    callback_query: CallbackQuery, state: FSMContext, page: int
):
    """Показать страницу с услугами"""
    async with SessionLocal() as session:
        services = await services_service.get_all_services(session)

    if not services:
        await callback_query.answer("Услуги пока не добавлены", show_alert=True)
        return

    # Пагинация: 5 услуг на страницу
    per_page = 5
    total_pages = (len(services) + per_page - 1) // per_page

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    services_on_page = services[start_idx:end_idx]

    kb = InlineKeyboardBuilder()
    for service in services_on_page:
        kb.row(
            InlineKeyboardButton(
                text=f"{service.name} - {service.price} руб. ({service.lenght} мин.)",
                callback_data=f"client.select_service|{service.id}",
            )
        )

    # Навигация
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⏪", callback_data=f"client.services_page|{page - 1}"
            )
        )
    else:
        nav_buttons.append(InlineKeyboardButton(text="⏪", callback_data="client.noop"))

    nav_buttons.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="client.noop")
    )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⏩", callback_data=f"client.services_page|{page + 1}"
            )
        )
    else:
        nav_buttons.append(InlineKeyboardButton(text="⏩", callback_data="client.noop"))

    kb.row(*nav_buttons)
    kb.row(InlineKeyboardButton(text="↩️ Назад", callback_data="client.main_menu"))

    await callback_query.message.edit_text(
        "Выберите услугу:", reply_markup=kb.as_markup()
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("client.services_page|"))
async def services_page_navigation(callback_query: CallbackQuery, state: FSMContext):
    """Навигация по страницам услуг"""
    page = int(callback_query.data.split("|")[1])
    await show_services_page(callback_query, state, page)


@router.callback_query(F.data == "client.noop")
async def noop_handler(callback_query: CallbackQuery):
    """Обработчик для неактивных кнопок"""
    await callback_query.answer()


@router.callback_query(F.data.startswith("client.select_service|"))
async def select_service(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора услуги - переход к выбору даты"""
    service_id = callback_query.data.split("|")[1]

    async with SessionLocal() as session:
        service = await services_service.get_service_by_id(session, service_id)
        if not service:
            await callback_query.answer("Услуга не найдена", show_alert=True)
            return

    # Сохраняем выбранную услугу
    await state.update_data(
        service_id=service_id,
        service_name=service.name,
        service_duration=service.lenght,
        service_price=service.price,
    )
    await state.set_state(NewOrderState.date)

    # Показываем сегодняшнюю дату
    today = datetime.now()
    await show_date_selection(callback_query, state, today.strftime("%Y-%m-%d"))


async def show_date_selection(
    callback_query: CallbackQuery, state: FSMContext, date_str: str
):
    """Показать выбор даты с навигацией"""
    data = await state.get_data()
    selected_date = datetime.strptime(date_str, "%Y-%m-%d")
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Создаем кнопки навигации
    kb = InlineKeyboardBuilder()

    # Кнопки навигации по датам
    prev_date = (selected_date - timedelta(days=1)).strftime("%Y-%m-%d")
    next_date = (selected_date + timedelta(days=1)).strftime("%Y-%m-%d")

    nav_buttons = []

    # Кнопка "назад" активна только если не сегодня
    if selected_date.date() > today.date():
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Предыдущий день",
                callback_data=f"client.navigate_date|{prev_date}",
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(
            text="Следующий день ▶️", callback_data=f"client.navigate_date|{next_date}"
        )
    )

    kb.row(*nav_buttons)

    # Кнопка подтверждения даты
    kb.row(
        InlineKeyboardButton(
            text="✅ Выбрать эту дату", callback_data=f"client.select_date|{date_str}"
        )
    )

    kb.row(InlineKeyboardButton(text="↩️ Назад", callback_data="client.new_order"))

    # Форматируем отображение даты
    display_date = selected_date.strftime("%d.%m.%Y")
    day_name = [
        "Понедельник",
        "Вторник",
        "Среда",
        "Четверг",
        "Пятница",
        "Суббота",
        "Воскресенье",
    ][selected_date.weekday()]

    if selected_date.date() == today.date():
        display_date = f"Сегодня ({display_date})"
    elif selected_date.date() == (today + timedelta(days=1)).date():
        display_date = f"Завтра ({display_date})"

    await callback_query.message.edit_text(
        f"Услуга: <b>{data['service_name']}</b>\n\n"
        f"📅 <b>{display_date}</b>\n"
        f"{day_name}\n\n"
        f"Используйте стрелки для выбора другой даты или нажмите ✅ для подтверждения.",
        reply_markup=kb.as_markup(),
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("client.navigate_date|"))
async def navigate_date(callback_query: CallbackQuery, state: FSMContext):
    """Навигация по датам"""
    date_str = callback_query.data.split("|")[1]
    await show_date_selection(callback_query, state, date_str)


@router.callback_query(F.data.startswith("client.select_date|"))
async def select_date(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора даты - переход к выбору времени"""
    date_str = callback_query.data.split("|")[1]
    selected_date = datetime.strptime(date_str, "%Y-%m-%d")

    # Сохраняем выбранную дату
    await state.update_data(selected_date=date_str)
    await state.set_state(NewOrderState.time)

    # Генерируем временные слоты
    time_slots = client_service.generate_time_slots(selected_date, step_minutes=30)

    # Фильтруем прошедшие слоты для сегодняшнего дня
    now = datetime.now()
    if selected_date.date() == now.date():
        time_slots = [slot for slot in time_slots if slot > now]

    if not time_slots:
        await callback_query.answer(
            "На сегодня все слоты заняты. Выберите другую дату.", show_alert=True
        )
        return

    # Создаем кнопки с временными слотами (по 3 в ряд)
    kb = InlineKeyboardBuilder()
    for slot in time_slots:
        time_str = slot.strftime("%H:%M")
        callback_data = f"client.select_time|{slot.strftime('%Y-%m-%d %H:%M')}"
        kb.button(text=time_str, callback_data=callback_data)

    kb.adjust(3)
    kb.row(
        InlineKeyboardButton(
            text="↩️ Назад",
            callback_data=f"client.navigate_date|{date_str}",
        )
    )

    data = await state.get_data()
    await callback_query.message.edit_text(
        f"Услуга: <b>{data['service_name']}</b>\n"
        f"Дата: <b>{selected_date.strftime('%d.%m.%Y')}</b>\n\n"
        f"Выберите время:",
        reply_markup=kb.as_markup(),
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("client.select_time|"))
async def select_time(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора времени - переход к выбору мастера"""
    time_str = callback_query.data.split("|")[1]
    selected_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")

    # Сохраняем выбранное время
    await state.update_data(selected_time=time_str)
    await state.set_state(NewOrderState.worker)

    data = await state.get_data()
    duration = data["service_duration"]

    # Получаем список свободных мастеров
    async with SessionLocal() as session:
        available_workers = await client_service.get_available_workers_at_time(
            session, selected_time, duration
        )

    if not available_workers:
        await callback_query.answer(
            "К сожалению, на это время нет свободных мастеров. Выберите другое время.",
            show_alert=True,
        )
        return

    # Создаем кнопки с мастерами
    kb = InlineKeyboardBuilder()
    for worker in available_workers:
        kb.row(
            InlineKeyboardButton(
                text=worker.name, callback_data=f"client.select_worker|{worker.id}"
            )
        )

    kb.row(
        InlineKeyboardButton(
            text="↩️ Назад", callback_data=f"client.select_date|{data['selected_date']}"
        )
    )

    await callback_query.message.edit_text(
        f"Услуга: <b>{data['service_name']}</b>\n"
        f"Дата: <b>{selected_time.strftime('%d.%m.%Y')}</b>\n"
        f"Время: <b>{selected_time.strftime('%H:%M')}</b>\n\n"
        f"Выберите мастера:",
        reply_markup=kb.as_markup(),
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith("client.select_worker|"))
async def select_worker(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора мастера - создание заказа"""
    worker_id = callback_query.data.split("|")[1]
    client_tg_id = callback_query.from_user.id

    data = await state.get_data()
    service_id = data["service_id"]
    selected_time_str = data["selected_time"]
    selected_time = datetime.strptime(selected_time_str, "%Y-%m-%d %H:%M")

    async with SessionLocal() as session:
        # Получаем ID клиента
        result = await session.execute(
            select(User.id, User.name).where(User.tg_id == client_tg_id)
        )
        client_data = result.one_or_none()
        if not client_data:
            await callback_query.answer(
                "Ошибка: пользователь не найден", show_alert=True
            )
            return

        client_id, client_name = client_data

        # Получаем данные мастера
        worker = await session.get(User, worker_id)
        if not worker:
            await callback_query.answer("Ошибка: мастер не найден", show_alert=True)
            return

        # Создаем заказ
        await client_service.create_client_order(
            session, str(client_id), worker_id, service_id, selected_time
        )

        # Формируем уведомление для мастера
        notification = client_service.format_order_notification(
            client_name, data["service_name"], selected_time, data["service_duration"]
        )

        # Формируем подтверждение для клиента
        confirmation = client_service.format_order_confirmation(
            worker.name,
            data["service_name"],
            selected_time,
            data["service_duration"],
            data["service_price"],
        )

    # Отправляем уведомление мастеру
    bot: Bot = callback_query.bot
    try:
        await bot.send_message(worker.tg_id, notification)
    except Exception:
        # Если не удалось отправить уведомление мастеру, продолжаем
        pass

    # Очищаем состояние
    await state.clear()

    # Отправляем подтверждение клиенту
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="↩️ В главное меню", callback_data="client.main_menu")
    )

    await callback_query.message.edit_text(confirmation, reply_markup=kb.as_markup())
    await callback_query.answer()
