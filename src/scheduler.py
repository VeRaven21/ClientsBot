import asyncio
from aiogram import Bot
from core.db import SessionLocal
from services import reminder_service


async def reminder_task(bot: Bot):
    """
    Фоновая задача для отправки напоминаний
    Запускается каждые 10 минут
    """
    while True:
        try:
            async with SessionLocal() as session:
                sent_count = await reminder_service.send_reminders(bot, session)
                if sent_count > 0:
                    print(f"Отправлено {sent_count} напоминаний")
        except Exception as e:
            print(f"Ошибка при отправке напоминаний: {e}")

        # Ждем 10 минут перед следующей проверкой
        await asyncio.sleep(600)


async def start_reminder_scheduler(bot: Bot):
    """Запустить планировщик напоминаний"""
    asyncio.create_task(reminder_task(bot))
