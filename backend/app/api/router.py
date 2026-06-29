from fastapi import APIRouter

from app.api.routes import alerts, auth, data_sources, dashboard, ingestion, settings, tenants, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(tenants.router)
api_router.include_router(users.router)
api_router.include_router(data_sources.router)
api_router.include_router(ingestion.router)
api_router.include_router(alerts.router)
api_router.include_router(dashboard.router)
api_router.include_router(settings.router)
