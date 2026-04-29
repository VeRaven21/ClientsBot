from aiogram import Router

from .main import router as main_router
from .orders import router as orders_router
from .services import router as services_router

# Главный роутер для работников
router = Router()
router.include_router(main_router)
router.include_router(orders_router)
router.include_router(services_router)

__all__ = ["router"]
