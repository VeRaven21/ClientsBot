import crud.services_crud as services_crud

from sqlalchemy.ext.asyncio import AsyncSession

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
