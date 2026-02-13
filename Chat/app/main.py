# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.websocket.chat_ws import router as chat_ws_router
from app.api.http.voice import router as voice_router
from app.api.http.offline import router as offline_router
from app.api.http.admin import router as admin_router
from app.db.session import init_db
from app.services.redis.session_store import init_redis


app = FastAPI(
    title="Agri AI Backend",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)

# CORS (important for mobile + web app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register Routers
app.include_router(chat_ws_router, prefix="/ws")
app.include_router(voice_router, prefix="/api")
app.include_router(offline_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    await init_db()
    await init_redis()
    print("🚀 Agri AI Backend Started")


@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Agri AI Backend Stopped")
