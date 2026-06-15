from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import socketio

from app.api.v1.routes import router
from app.core.config import get_settings
from app.database.indexes import create_indexes
from app.database.mongodb import close_mongo_connection, connect_to_mongo
from app.services.message_service import MessageService
from app.services.notification_service import NotificationService
from app.websocket.manager import manager, sio

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await create_indexes()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    notification_service = NotificationService()
    notification_service.set_socket_manager(manager)
    message_service = MessageService()
    message_service.set_socket_manager(manager)

    yield

    try:
        await close_mongo_connection()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_TAGLINE,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_V1_PREFIX)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "tagline": settings.APP_TAGLINE, "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
