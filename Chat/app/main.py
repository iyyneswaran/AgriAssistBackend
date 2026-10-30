from fastapi import Depends, FastAPI, Request
from app.core.security import authenticated_user
from app.middleware.body_limit import BodySizeLimit
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
from app.api.http.scan import router as scan_router
from app.notifications.routes.push_routes import router as push_router
from app.notifications.routes.notification_routes import router as notification_router
from app.notifications.routes.preference_routes import router as preference_router


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agri AI Backend",
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
)


# ── Lightweight health endpoint (no ML, no DB, no rate limit) ──
@app.get("/health")
async def health_check():
    return {"ok": True}


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

# CORS (configured for local dev + Vercel production frontend)
allowed_origins_list = [
    "https://agri-assist-frontend-seven.vercel.app",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
]
if settings.ALLOWED_ORIGINS:
    for o in settings.ALLOWED_ORIGINS.split(","):
        o = o.strip()
        if o and o != '*' and o not in allowed_origins_list:
            allowed_origins_list.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register Routers
app.add_middleware(BodySizeLimit)
app.include_router(chat_ws_router, prefix="/ws")
app.include_router(chat_router, prefix="/api", dependencies=[Depends(authenticated_user)])
app.include_router(voice_router, prefix="/api", dependencies=[Depends(authenticated_user)])
app.include_router(offline_router, prefix="/api", dependencies=[Depends(authenticated_user)])
app.include_router(admin_router, prefix="/api")
app.include_router(geo_router, dependencies=[Depends(authenticated_user)])
app.include_router(schemes_router, prefix="/api")
app.include_router(sensor_router, prefix="/api")
app.include_router(scan_router, prefix="/api", dependencies=[Depends(authenticated_user)])

# Notification system routes
app.include_router(push_router, prefix="/api")
app.include_router(notification_router, prefix="/api")
app.include_router(preference_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.warning(
            "Supabase is not configured. Scheme recommendation and RAG features are disabled. "
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to enable them."
        )
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Database initialization failed at startup: {e}")
    try:
        await init_redis()
    except Exception as e:
        logger.error(f"Redis initialization failed at startup: {e}")
    # NOTE: Crop disease detection model is now lazy-loaded on first /api/scan request
    # instead of blocking startup. This lets uvicorn bind to PORT quickly on Railway.
    print("[OK] Crop Disease Detection Model will be loaded on first scan request (lazy)")
    # Notification system
    if settings.VITE_VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY:
        print("[OK] Push Notification System Ready (VAPID configured)")
    else:
        print("[WARN] Push Notifications: VAPID keys not configured")
    print("[OK] Agri AI Backend Started")


@app.on_event("shutdown")
async def shutdown_event():
    print("[STOP] Agri AI Backend Stopped")
