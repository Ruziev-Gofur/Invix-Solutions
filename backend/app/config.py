from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str  # postgresql+asyncpg://user:pass@host:5432/db
    minio_endpoint: str = "minio:9000"
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "products"
    minio_secure: bool = False
    bot_api_secret: str  # общий секрет бота и API
    max_image_mb: int = Field(default=10, ge=1, le=50)


settings = Settings()
