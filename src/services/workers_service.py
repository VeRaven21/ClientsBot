from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, UserRoleEnum, Order
from typing import List
import crud.workers_crud as workers_crud


async def get_all_workers(session: AsyncSession) -> List[User]:
    """Получить список всех сотрудников"""
    return await workers_crud.get_workers_list(session)


async def get_workers_count(session: AsyncSession) -> int:
    """Получить количество сотрудников"""
    return await workers_crud.get_workers_count(session)


async def get_worker_info(session: AsyncSession, worker_id: str) -> dict | None:
    """Получить информацию о сотруднике"""
    worker = await workers_crud.get_worker_by_id(session, worker_id)
    if not worker or worker.role != UserRoleEnum.WORKER:
        return None

    orders_count = await workers_crud.get_worker_orders_count(session, worker_id)

    return {
        "worker": worker,
        "orders_count": orders_count,
    }


async def get_worker_orders(
    session: AsyncSession, worker_id: str, limit: int = 10
) -> List[Order]:
    """Получить последние заказы сотрудника"""
    return await workers_crud.get_worker_recent_orders(session, worker_id, limit)


async def remove_worker(session: AsyncSession, worker_id: str) -> bool:
    """Удалить сотрудника (изменить роль на CLIENT)"""
    worker = await workers_crud.get_worker_by_id(session, worker_id)
    if not worker or worker.role != UserRoleEnum.WORKER:
        return False

    return await workers_crud.change_user_role(session, worker_id, UserRoleEnum.CLIENT)


async def add_worker_by_tg_id(
    session: AsyncSession, tg_id: int
) -> tuple[bool, str, User | None]:
    """
    Добавить сотрудника по Telegram ID
    Возвращает: (успех, сообщение, пользователь)
    """
    # Ищем пользователя в базе
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()

    if not user:
        return False, "Пользователь не найден в базе данных", None

    if user.role == UserRoleEnum.WORKER:
        return False, f"{user.name} уже является сотрудником", user

    if user.role == UserRoleEnum.ADMIN:
        return False, f"{user.name} является администратором", user

    # Меняем роль на WORKER
    success = await workers_crud.change_user_role(
        session, str(user.id), UserRoleEnum.WORKER
    )

    if success:
        return True, f"{user.name} успешно добавлен в список сотрудников", user
    else:
        return False, "Ошибка при изменении роли", user


async def add_worker_by_username(
    session: AsyncSession, username: str
) -> tuple[bool, str, User | None]:
    """
    Добавить сотрудника по username
    Возвращает: (успех, сообщение, пользователь)
    """
    user = await workers_crud.get_user_by_username(session, username)

    if not user:
        return (
            False,
            f"Пользователь @{username} не найден в базе данных",
            None,
        )

    if user.role == UserRoleEnum.WORKER:
        return False, f"{user.name} уже является сотрудником", user

    if user.role == UserRoleEnum.ADMIN:
        return False, f"{user.name} является администратором", user

    # Меняем роль на WORKER
    success = await workers_crud.change_user_role(
        session, str(user.id), UserRoleEnum.WORKER
    )

    if success:
        return True, f"{user.name} успешно добавлен в список сотрудников", user
    else:
        return False, "Ошибка при изменении роли", user


def format_workers_list_for_pagination(
    workers: List[User], page: int, per_page: int = 5
) -> tuple[List[User], int]:
    """
    Форматировать список сотрудников для пагинации
    Возвращает: (список сотрудников на странице, общее количество страниц)
    """
    total_workers = len(workers)
    total_pages = (total_workers + per_page - 1) // per_page

    # Проверяем, что страница в допустимых пределах
    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages

    start = (page - 1) * per_page
    end = start + per_page

    return workers[start:end], total_pages
