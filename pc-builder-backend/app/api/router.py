from fastapi import APIRouter

from app.api.routes import (
    admin,
    analysis,
    auth,
    benchmarks,
    builds,
    catalog,
    harvester,
    health,
    notifications,
    products,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(notifications.router)
api_router.include_router(builds.router)
api_router.include_router(catalog.router)
api_router.include_router(analysis.router)
api_router.include_router(benchmarks.router)
api_router.include_router(admin.router)
api_router.include_router(harvester.router)
