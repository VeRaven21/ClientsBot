import crud.services_crud as services_crud

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Tuple

from models.services import ServicesResponse, ServiceSchema

from database.models import Service


async def get_services(session: AsyncSession) -> ServicesResponse:
    services = await services_crud.get_services(session)

    services_list = []

    for sercvice in services:
        services_list.append(
            ServiceSchema(id=sercvice.id, name=sercvice.name, price=sercvice.price)
        )

    return ServicesResponse(services=services_list, count=len(services_list))


async def get_all_services(session: AsyncSession) -> List[Service]:
    """Получить список всех услуг"""
    return await services_crud.get_services(session)


async def add_service(
    session: AsyncSession, name: str, price: int, lenght: int
) -> bool:
    if await services_crud.get_service_by_name(session, name) is not None:
        return False
    new_service = Service(name=name, price=price, lenght=lenght)
    await services_crud.add_service(session, new_service)
    return True


async def delete_service(session: AsyncSession, service_id: str) -> bool:
    service = await session.get(Service, service_id)
    if service is None:
        return False
    await session.delete(service)
    await session.commit()
    return True


async def get_service_by_name(session: AsyncSession, name: str) -> Service | None:
    """Получить услугу по названию"""
    return await services_crud.get_service_by_name(session, name)


async def get_service_by_id(session: AsyncSession, service_id: str) -> Service | None:
    """Получить услугу по ID"""
    return await session.get(Service, service_id)


async def update_service_field(
    session: AsyncSession, service_id: str, field: str, value: str | int
) -> Tuple[bool, str]:
    """
    Обновить поле услуги
    Возвращает: (успех, сообщение об ошибке)
    """
    service = await session.get(Service, service_id)
    if not service:
        return False, "Услуга не найдена"

    if field == "name":
        # Проверяем, не существует ли услуга с таким названием
        existing = await get_service_by_name(session, str(value))
        if existing and str(existing.id) != service_id:
            return False, f"Услуга с названием '{value}' уже существует"
        service.name = str(value)
    elif field == "price":
        try:
            price = int(value)
            if price <= 0:
                return False, "Цена должна быть положительным числом"
            service.price = price
        except ValueError:
            return False, "Цена должна быть целым числом"
    elif field == "lenght":
        try:
            lenght = int(value)
            if lenght <= 0:
                return False, "Длительность должна быть положительным числом"
            service.lenght = lenght
        except ValueError:
            return False, "Длительность должна быть целым числом"
    else:
        return False, "Неизвестное поле"

    await session.commit()
    return True, ""


def format_services_list_for_pagination(
    services: List[Service], page: int, per_page: int = 5
) -> Tuple[List[Service], int]:
    """
    Форматировать список услуг для пагинации
    Возвращает: (список услуг на странице, общее количество страниц)
    """
    total_services = len(services)
    total_pages = (total_services + per_page - 1) // per_page

    # Проверяем, что страница в допустимых пределах
    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages

    start = (page - 1) * per_page
    end = start + per_page

    return services[start:end], total_pages
