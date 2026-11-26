import asyncio
import logging
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])

Check = Callable[[], Awaitable[None]]


@router.get("", include_in_schema=False)
@router.get("/live")
async def liveness_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/ready")
async def rediness_check() -> JSONResponse:
    database_result, redis_result = await asyncio.gather(
        _run_check("database", _check_database),
        _run_check("redis", _check_redis),
    )

    checks = {
        "database": database_result,
        "redis": redis_result,
    }
    ready = all(result["status"] == "ok" for result in checks.values())

    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ok" if ready else "unavailable",
            "checks": checks,
        },
    )


@router.get("/db", include_in_schema=False)
async def database_health_check() -> JSONResponse:
    result = await _run_check("database", _check_database)
    healthy = result["status"] == "ok"

    return JSONResponse(
        status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ok" if healthy else "unavailable",
            "database": result["status"],
        },
    )


async def _run_check(name: str, check: Check) -> dict[str, str]:
    try:
        async with asyncio.timeout(3):
            await check()
    except Exception as exc:
        logger.warning(
            "dependency_health_check_failed",
            extra={
                "event": "dependency_health_check_failed",
                "dependency": name,
                "error_type": type(exc).__name__,
            },
        )
        return {"status": "unavailable"}

    return {"status": "ok"}


async def _check_database() -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def _check_redis() -> None:
    client = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )

    try:
        await client.ping()
    finally:
        await client.aclose()
