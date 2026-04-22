from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models.users.users import Client

import services.client_service as client_service
import services.job_service as job_service
import services.workers_service as workers_service

router = Router()

def menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Профиль", callback_data="show_data")
    kb.button(text="Посмотреть доступные услуги", callback_data="services_list")
    kb.button(text="Заказать услугу", callback_data="order_service")
    kb.adjust(1)  # 1 кнопка в ряд
    return kb.as_markup()


@router.message(CommandStart())
@router.message(F.text == "Главное меню")
async def start_command(message: Message):
    await message.answer("Привет!", reply_markup=menu_kb())

@router.callback_query(F.data == "main_menu")
async def main_menu(cb: CallbackQuery):
    await cb.answer()
    if cb.message is None:
        return
    await cb.message.edit_text("Главное меню", reply_markup=menu_kb())

@router.callback_query(F.data == "show_data")
async def show_data(cb: CallbackQuery):
    await cb.answer()
    if cb.message is None:
        return

    user_id = cb.from_user.id
    client: Client = await client_service.get_client_by_telegram_id(user_id)

    if client:
        text = (
            f"Имя: {client.name}\n"
            f"Id: {client.tg_id}\n"
            f"Id в базе: {client.id}"
        )   
    kb = InlineKeyboardBuilder()
    kb.button(text="Назад", callback_data="main_menu")
    kb.adjust(1)
    if client:
        await cb.message.edit_text(text, reply_markup=kb.as_markup())
    else:
        await cb.message.edit_text("Данные не найдены. Пожалуйста, зарегистрируйтесь.", reply_markup=menu_kb())


@router.callback_query(F.data == "services_list")
async def services_list(cb: CallbackQuery):
    await cb.answer()
    if cb.message is None:
        return

    services = await job_service.get_all_services()
    if services:
        text = "Доступные услуги:\n\n"
        for service in services:
            text += f"- {service.name} - {service.price} рублей - {service.lenght} минут\n"
    else:
        text = "Сейчас нет доступных услуг"

    kb = InlineKeyboardBuilder()
    kb.button(text="Назад", callback_data="main_menu")
    kb.adjust(1)

    await cb.message.edit_text(text, reply_markup=kb.as_markup())

class OrderServiceState(StatesGroup):
    chosen_service = State()
    chosen_time = State()
    chosen_worker = State()

@router.callback_query(F.data == "order_service")
async def order_service(cb: CallbackQuery, state: FSMContext):
    text = "Выберите услугу:"
    services = await job_service.get_all_services()
    kb = InlineKeyboardBuilder()

    for service in services:
        kb.button(text=f"{service.name} - {service.price} рублей - {service.lenght} минут", callback_data=f"service_{service.id}")
    kb.adjust(1)

    await cb.answer()
    if cb.message is None:
        return
    
    await cb.message.edit_text(text, reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("service_"))
async def choose_service(cb: CallbackQuery, state: FSMContext):
    service_id: str = cb.data.split("_")[1]
    await state.update_data(chosen_service=service_id)

    text = f"Выбрана услуга {service_id}. Выберите мастера:"
    kb = InlineKeyboardBuilder()
    kb.button(text="Назад", callback_data="order_service")
    kb.adjust(1)

    masters = await workers_service.get_all_workers()
    for master in masters:
        kb.button(text=master.name, callback_data=f"worker_{master.id}")
    kb.adjust(1)

    await cb.answer()
    if cb.message is None:
        return
    await cb.message.edit_text(text, reply_markup=kb.as_markup())


