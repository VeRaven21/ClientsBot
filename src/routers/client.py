from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

import services.client_service as client_service

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    try:
        added: bool = await client_service.create_client(message)
        if added:
            await message.answer(
                "Welcome to the Clients Bot! Your data has been saved.",
                message_effect_id="5046509860389126442",
            )
        else:
            await message.answer("You are already registered.")
    except Exception as e:
        await message.answer(f"Error {e}")
