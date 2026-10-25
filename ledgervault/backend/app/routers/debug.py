import os

from fastapi import APIRouter

from ..config import settings

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/config")
def debug_config():
    return {
        "debug": settings.DEBUG,
        "database_url": settings.DATABASE_URL,
        "redis_url": settings.REDIS_URL,
        "jwt_secret": settings.JWT_SECRET,
        "bootstrap_token": settings.BOOTSTRAP_TOKEN,
        "s3": {
            "endpoint": settings.S3_ENDPOINT,
            "access_key": settings.S3_ACCESS_KEY,
            "secret_key": settings.S3_SECRET_KEY,
        },
        "env": dict(os.environ),
    }
