from database.models.users.users import Client
from crud import user as user_crud
from aiogram.types import Message


async def create_client(message: Message) -> bool:
    client = Client(name=message.from_user.full_name, tg_id=message.from_user.id)
    user_exists = await user_crud.get_user_by_tg_id(client.tg_id)
    if not user_exists:
        await user_crud.add_user(client)
        return True
    return False


async def get_client_by_telegram_id(tg_id: int) -> Client | None:
    return await user_crud.get_user_by_tg_id(tg_id)
