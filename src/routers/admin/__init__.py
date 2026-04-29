from aiogram import Router

from .main import router as main_router
from .services import router as services_router
from .users import router as users_router
from .orders import router as orders_router
from .workers import router as workers_router

# Главный роутер для админки
router = Router()
router.include_router(main_router)
router.include_router(services_router)
router.include_router(users_router)
router.include_router(orders_router)
router.include_router(workers_router)

__all__ = ["router"]
