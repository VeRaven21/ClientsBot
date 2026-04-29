from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Service
from typing import List


async def get_services(session: AsyncSession) -> List[Service]:
    services = await session.execute(select(Service))

    return services.scalars().all()


async def get_service_by_name(session: AsyncSession, name: str) -> Service | None:
    service = await session.execute(select(Service).where(Service.name == name))
    return service.scalar_one_or_none()


async def add_service(session: AsyncSession, service: Service) -> None:
    session.add(service)
    await session.commit()


async def delete_service(session: AsyncSession, service_id: str) -> None:
    service = await session.get(Service, service_id)
    if service:
        await session.delete(service)
        await session.commit()
