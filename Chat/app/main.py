from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.websocket.chat_ws import router as chat_ws_router
from app.api.http.voice import router as voice_router
from app.api.http.chat import router as chat_router
from app.api.http.offline import router as offline_router
from app.api.http.admin import router as admin_router
from app.db.session import init_db
from app.services.redis.session_store import init_redis
import traceback
import logging
from app.api.http.geo import router as geo_router
from app.api.http.schemes import router as schemes_router
from app.api.http.sensor import router as sensor_router


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agri AI Backend",
    version="1.0.0",
    debug=True,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)


# Debug: show actual errors instead of generic 500
if settings.DEBUG:
    @app.exception_handler(Exception)
    async def debug_exception_handler(request: Request, exc: Exception):
        tb = traceback.format_exc()
        logger.error(f"Unhandled error: {tb}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "traceback": tb},
        )

# CORS (important for mobile + web app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register Routers
app.include_router(chat_ws_router, prefix="/ws")
app.include_router(chat_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(offline_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(geo_router)
app.include_router(schemes_router, prefix="/api")
app.include_router(sensor_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    await init_db()
    await init_redis()
    print("[OK] Agri AI Backend Started")


@app.on_event("shutdown")
async def shutdown_event():
    print("[STOP] Agri AI Backend Stopped")
