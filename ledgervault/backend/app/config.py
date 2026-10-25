import os


class Settings:
    """Runtime configuration, sourced from environment variables with
    development-friendly defaults."""

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://ledger:ledger@db:5432/ledgervault"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Object storage (MinIO / S3-compatible)
    S3_ENDPOINT: str = os.getenv("S3_ENDPOINT", "http://minio:9000")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "ledgervault")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "minioadmin")

    # Auth
    JWT_SECRET: str = os.getenv("JWT_SECRET", "devsecret123")
    JWT_TTL_SECONDS: int = int(os.getenv("JWT_TTL_SECONDS", "86400"))

    # Behaviour flags
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    SEED_ON_START: bool = os.getenv("SEED_ON_START", "true").lower() == "true"

    # Internal bootstrap endpoint used by the metadata service during
    # provisioning. Not intended for end users.
    BOOTSTRAP_TOKEN: str = os.getenv("BOOTSTRAP_TOKEN", "bootstrap-provisioning-7f3a")

    FILE_STORAGE_DIR: str = os.getenv("FILE_STORAGE_DIR", "/srv/files")


settings = Settings()
