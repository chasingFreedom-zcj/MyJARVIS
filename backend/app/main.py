from fastapi import FastAPI

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.request_context import RequestContextMiddleware
from app.routers.chat import router as chat_router
from app.routers.conversation import router as conversation_router
from app.routers.goal import router as goal_router
from app.routers.health import router as health_router
from app.routers.message import router as message_router
from app.routers.profiles import router as profile_router

configure_logging(settings.log_level)

app = FastAPI(title="MyJARVIS", description="A simple JARVIS API", version="0.1.0")
app.add_middleware(RequestContextMiddleware)
register_exception_handlers(app)


@app.get("/")
async def root():
    return {
        "name": "JARVIS",
        "message": "Hello, I'm JARVIS! Your personal AI assistant.",
    }


app.include_router(profile_router)
app.include_router(goal_router)
app.include_router(conversation_router)
app.include_router(message_router)
app.include_router(chat_router)
app.include_router(health_router)
app.include_router(profile_router)
