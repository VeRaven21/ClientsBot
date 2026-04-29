from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from models import ServicesResponse
from services import services_service
from core.db import SessionLocal
from database.models import Service

router = Router()


async def services_list_page(page: int, button_prefix: str) -> InlineKeyboardBuilder:
    """Создает клавиатуру со списком услуг с пагинацией"""
    async with SessionLocal() as session:
        services: ServicesResponse = await services_service.get_services(session)

    kb = InlineKeyboardBuilder()
    total_services = len(services.services)
    total_pages = (total_services + 4) // 5  # Округление вверх для 5 услуг на страницу

    # Проверяем, что страница в допустимых пределах
    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages

    start = (page - 1) * 5
    end = start + 5

    # Добавляем кнопки услуг по одной в строке
    for service in services.services[start:end]:
        kb.row(
            InlineKeyboardButton(
                text=f"{service.name} - {service.price} руб.",
                callback_data=f"{button_prefix}|{service.id}",
            )
        )

    # Добавляем кнопки управления в одну строку
    # Кнопка "назад" активна только если не на первой странице
    # Кнопка "вперед" активна только если не на последней странице
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


async def services_management_menu() -> InlineKeyboardBuilder:
    """Создает клавиатуру меню управления услугами"""
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить услугу", callback_data="admin.add_service")
    kb.button(text="Редактировать услугу", callback_data="admin.edit_service")
    kb.adjust(2)
    kb.button(text="Назад", callback_data="admin.main_menu")
    kb.adjust(1)
    return kb


async def service_edit_menu() -> InlineKeyboardBuilder:
    """Создает клавиатуру меню редактирования услуги"""
    kb = InlineKeyboardBuilder()
    kb.button(text="Редактировать услугу", callback_data="admin.edit_service.edit")
    kb.button(text="Удалить услугу", callback_data="admin.edit_service.delete")
    kb.adjust(2)
    kb.button(text="Назад", callback_data="admin.services_management")
    kb.adjust(1)
    return kb


class AddServiceState(StatesGroup):
    """Состояния для добавления услуги"""

    name = State()
    price = State()
    lenght = State()


class EditServiceState(StatesGroup):
    """Состояния для редактирования услуги"""

    service_id = State()
    field = State()
    value = State()


@router.callback_query(F.data == "admin.services_management")
async def services_management(callback_query: CallbackQuery):
    """Обработчик меню управления услугами"""
    async with SessionLocal() as session:
        services_response: ServicesResponse = await services_service.get_services(
            session
        )
        kb = await services_management_menu()
        text = f"Услуг в списке: <b>{services_response.count}</b>\nВыберите действие:"
    await callback_query.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "admin.add_service")
async def add_service(callback_query: CallbackQuery, state: FSMContext):
    """Начало процесса добавления услуги"""
    await state.set_state(AddServiceState.name)
    # Создаем клавиатуру с кнопкой "Отмена"
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
    )
    await callback_query.message.answer(
        "Введите название услуги:", reply_markup=cancel_kb
    )
    await callback_query.answer()


@router.message(F.text == "Отмена", StateFilter(AddServiceState))
async def cancel_add_service(message: Message, state: FSMContext):
    """Отмена добавления услуги"""
    await state.clear()
    await message.answer(
        "Добавление услуги отменено.", reply_markup=ReplyKeyboardRemove()
    )
    kb = await services_management_menu()
    text = "Выберите действие:"
    await message.answer(text, reply_markup=kb.as_markup())


@router.message(AddServiceState.name)
async def process_service_name(message: Message, state: FSMContext):
    """Обработка названия услуги"""
    await state.update_data(name=message.text)
    await state.set_state(AddServiceState.price)
    # Кнопка "Отмена" остается
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
    )
    await message.answer("Введите стоимость услуги:", reply_markup=cancel_kb)


@router.message(AddServiceState.price)
async def process_service_price(message: Message, state: FSMContext):
    """Обработка стоимости услуги"""
    try:
        price = int(message.text)
        if price <= 0:
            cancel_kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
            )
            await message.answer(
                "Стоимость должна быть положительным числом. Попробуйте еще раз:",
                reply_markup=cancel_kb,
            )
            return
        await state.update_data(price=price)
        await state.set_state(AddServiceState.lenght)
        # Кнопка "Отмена" остается
        cancel_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
        )
        await message.answer(
            "Введите длительность услуги (в минутах):", reply_markup=cancel_kb
        )
    except ValueError:
        cancel_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
        )
        await message.answer(
            "Стоимость должна быть целым числом. Попробуйте еще раз:",
            reply_markup=cancel_kb,
        )


@router.message(AddServiceState.lenght)
async def process_service_lenght(message: Message, state: FSMContext):
    """Обработка длительности услуги и сохранение в БД"""
    try:
        lenght = int(message.text)
        if lenght <= 0:
            cancel_kb = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
            )
            await message.answer(
                "Длительность должна быть положительным числом. Попробуйте еще раз:",
                reply_markup=cancel_kb,
            )
            return

        data = await state.get_data()
        name = data.get("name")
        price = data.get("price")

        async with SessionLocal() as session:
            flag = await services_service.add_service(session, name, price, lenght)

        if flag:
            await message.answer(
                f"Услуга '{name}' успешно добавлена", reply_markup=ReplyKeyboardRemove()
            )
        else:
            await message.answer(
                f"Услуга с названием '{name}' уже существует. Попробуйте другое название.",
                reply_markup=ReplyKeyboardRemove(),
            )

        await state.clear()
        kb = await services_management_menu()
        text = "Выберите действие:"
        await message.answer(text, reply_markup=kb.as_markup())
    except ValueError:
        cancel_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
        )
        await message.answer(
            "Длительность должна быть целым числом. Попробуйте еще раз:",
            reply_markup=cancel_kb,
        )


@router.callback_query(F.data == "admin.edit_service")
async def edit_service(callback_query: CallbackQuery):
    """Показать меню редактирования услуги"""
    kb = await service_edit_menu()
    await callback_query.message.edit_text(
        "Выберите действие:", reply_markup=kb.as_markup()
    )


@router.callback_query(F.data == "admin.edit_service.edit")
async def edit_service_choose(callback_query: CallbackQuery):
    """Показать список услуг для редактирования"""
    kb = await services_list_page(1, "admin.edit_service_select")
    await callback_query.message.edit_text(
        "Выберите услугу для редактирования:", reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.startswith("admin.edit_service_select|"))
async def edit_service_select_action(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора услуги для редактирования"""
    parts = callback_query.data.split("|")

    # Обработка noop (неактивные кнопки)
    if len(parts) >= 2 and parts[1] == "noop":
        await callback_query.answer()
        return

    # Обработка выбора услуги
    if len(parts) >= 2 and parts[1] not in ("back", "prev", "next", "noop"):
        service_id = parts[1]

        # Получаем информацию об услуге
        async with SessionLocal() as session:
            service = await session.get(Service, service_id)
            if not service:
                await callback_query.answer("Услуга не найдена", show_alert=True)
                return

        # Сохраняем ID услуги в состояние
        await state.update_data(service_id=service_id)
        await state.set_state(EditServiceState.field)

        # Показываем меню выбора поля для редактирования
        kb = InlineKeyboardBuilder()
        kb.row(
            InlineKeyboardButton(text="Название", callback_data="admin.edit_field|name")
        )
        kb.row(
            InlineKeyboardButton(text="Цена", callback_data="admin.edit_field|price")
        )
        kb.row(
            InlineKeyboardButton(
                text="Длительность", callback_data="admin.edit_field|lenght"
            )
        )
        kb.row(
            InlineKeyboardButton(text="Отмена", callback_data="admin.edit_service.edit")
        )

        await callback_query.message.edit_text(
            f"Услуга: <b>{service.name}</b>\n"
            f"Цена: <b>{service.price}</b> руб.\n"
            f"Длительность: <b>{service.lenght}</b> мин.\n\n"
            f"Что хотите изменить?",
            reply_markup=kb.as_markup(),
        )

    # Обработка кнопки "назад"
    elif len(parts) >= 2 and parts[1] == "back":
        kb = await service_edit_menu()
        await callback_query.message.edit_text(
            "Выберите действие:", reply_markup=kb.as_markup()
        )

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
        kb = await services_list_page(page, "admin.edit_service_select")
        await callback_query.message.edit_text(
            "Выберите услугу для редактирования:", reply_markup=kb.as_markup()
        )


@router.callback_query(F.data.startswith("admin.edit_field|"))
async def edit_field_selected(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора поля для редактирования"""
    field = callback_query.data.split("|")[1]
    await state.update_data(field=field)

    field_names = {"name": "название", "price": "цену", "lenght": "длительность"}

    # Создаем клавиатуру с кнопкой "Отмена"
    cancel_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
    )

    await callback_query.message.answer(
        f"Введите новое значение для поля <b>{field_names[field]}</b>:",
        reply_markup=cancel_kb,
    )
    await state.set_state(EditServiceState.value)
    await callback_query.answer()


@router.message(F.text == "Отмена", StateFilter(EditServiceState))
async def cancel_edit_service(message: Message, state: FSMContext):
    """Отмена редактирования услуги"""
    await state.clear()
    await message.answer(
        "Редактирование услуги отменено.", reply_markup=ReplyKeyboardRemove()
    )
    kb = await services_management_menu()
    text = "Выберите действие:"
    await message.answer(text, reply_markup=kb.as_markup())


@router.message(EditServiceState.value)
async def process_edit_value(message: Message, state: FSMContext):
    """Обработка нового значения поля"""
    data = await state.get_data()
    service_id = data.get("service_id")
    field = data.get("field")
    new_value = message.text

    try:
        async with SessionLocal() as session:
            service = await session.get(Service, service_id)
            if not service:
                await message.answer(
                    "Услуга не найдена", reply_markup=ReplyKeyboardRemove()
                )
                await state.clear()
                return

            # Валидация и обновление поля
            if field == "name":
                # Проверяем, не существует ли услуга с таким названием
                existing = await services_service.get_service_by_name(
                    session, new_value
                )
                if existing and str(existing.id) != service_id:
                    cancel_kb = ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
                    )
                    await message.answer(
                        f"Услуга с названием '{new_value}' уже существует. Попробуйте другое название:",
                        reply_markup=cancel_kb,
                    )
                    return
                service.name = new_value
            elif field == "price":
                try:
                    price = int(new_value)
                    if price <= 0:
                        cancel_kb = ReplyKeyboardMarkup(
                            keyboard=[[KeyboardButton(text="Отмена")]],
                            resize_keyboard=True,
                        )
                        await message.answer(
                            "Цена должна быть положительным числом. Попробуйте еще раз:",
                            reply_markup=cancel_kb,
                        )
                        return
                    service.price = price
                except ValueError:
                    cancel_kb = ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
                    )
                    await message.answer(
                        "Цена должна быть целым числом. Попробуйте еще раз:",
                        reply_markup=cancel_kb,
                    )
                    return
            elif field == "lenght":
                try:
                    lenght = int(new_value)
                    if lenght <= 0:
                        cancel_kb = ReplyKeyboardMarkup(
                            keyboard=[[KeyboardButton(text="Отмена")]],
                            resize_keyboard=True,
                        )
                        await message.answer(
                            "Длительность должна быть положительным числом. Попробуйте еще раз:",
                            reply_markup=cancel_kb,
                        )
                        return
                    service.lenght = lenght
                except ValueError:
                    cancel_kb = ReplyKeyboardMarkup(
                        keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True
                    )
                    await message.answer(
                        "Длительность должна быть целым числом. Попробуйте еще раз:",
                        reply_markup=cancel_kb,
                    )
                    return

            await session.commit()

            field_names = {
                "name": "Название",
                "price": "Цена",
                "lenght": "Длительность",
            }

            await message.answer(
                f"{field_names[field]} услуги успешно обновлено!",
                reply_markup=ReplyKeyboardRemove(),
            )

    except Exception as e:
        await message.answer(
            f"Произошла ошибка при обновлении: {str(e)}",
            reply_markup=ReplyKeyboardRemove(),
        )

    await state.clear()
    kb = await services_management_menu()
    text = "Выберите действие:"
    await message.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "admin.edit_service.delete")
async def delete_service_choose(callback_query: CallbackQuery):
    """Показать список услуг для удаления"""
    kb = await services_list_page(1, "admin.delete_service")
    await callback_query.message.edit_text(
        "Выберите услугу для удаления:", reply_markup=kb.as_markup()
    )


@router.callback_query(F.data.startswith("admin.delete_service|"))
async def delete_service_action(callback_query: CallbackQuery):
    """Обработка удаления услуги"""
    parts = callback_query.data.split("|")

    # Обработка noop (неактивные кнопки)
    if len(parts) >= 2 and parts[1] == "noop":
        await callback_query.answer()
        return

    # Обработка удаления услуги
    if len(parts) >= 2 and parts[1] not in ("back", "prev", "next", "noop"):
        service_id = parts[1]
        async with SessionLocal() as session:
            flag = await services_service.delete_service(session, service_id)
        if flag:
            await callback_query.answer("Услуга успешно удалена", show_alert=True)
            # Показываем обновленный список услуг
            kb = await services_list_page(1, "admin.delete_service")
            await callback_query.message.edit_text(
                "Выберите услугу для удаления:", reply_markup=kb.as_markup()
            )
        else:
            await callback_query.answer(
                "Ошибка: услуга не найдена или не удалена.", show_alert=True
            )
    # Обработка кнопки "назад"
    elif len(parts) >= 2 and parts[1] == "back":
        kb = await service_edit_menu()
        await callback_query.message.edit_text(
            "Выберите действие:", reply_markup=kb.as_markup()
        )
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
        kb = await services_list_page(page, "admin.delete_service")
        await callback_query.message.edit_text(
            "Выберите услугу для удаления:", reply_markup=kb.as_markup()
        )
