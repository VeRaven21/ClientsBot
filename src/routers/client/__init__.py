from aiogram import Router

from .main import router as main_router
from .orders import router as orders_router
from .new_order import router as new_order_router

# Главный роутер для клиентской части
router = Router()
router.include_router(main_router)
router.include_router(orders_router)
router.include_router(new_order_router)

__all__ = ["router"]
