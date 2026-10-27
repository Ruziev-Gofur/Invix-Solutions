import io
import logging
import re
import secrets
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from minio.error import S3Error
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import storage
from .config import settings
from .db import Base, engine, get_session
from .models import Product
from .schemas import ProductOut

ALLOWED = {"JPEG": ("jpg", "image/jpeg"), "PNG": ("png", "image/png"), "WEBP": ("webp", "image/webp")}
KEY_RE = re.compile(r"[a-f0-9]{32}\.(jpg|png|webp)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Для продакшена вместо create_all лучше Alembic-миграции
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await run_in_threadpool(storage.ensure_bucket)
    yield
    await engine.dispose()


app = FastAPI(title="Catalog API", lifespan=lifespan)


def require_bot(x_bot_secret: Annotated[str | None, Header()] = None) -> None:
    given = (x_bot_secret or "").encode()
    if not secrets.compare_digest(given, settings.bot_api_secret.encode()):
        raise HTTPException(status_code=403, detail="Forbidden")


def detect_image(data: bytes) -> tuple[str, str]:
    """Проверяем по содержимому, а не по Content-Type из запроса."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = img.format
            img.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(status_code=415, detail="Файл не является изображением")
    if fmt not in ALLOWED:
        raise HTTPException(status_code=415, detail="Допустимы JPEG, PNG и WEBP")
    return ALLOWED[fmt]


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.get("/api/products", response_model=list[ProductOut])
async def list_products(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    stmt = (
        select(Product)
        .order_by(Product.created_at.desc(), Product.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return (await session.scalars(stmt)).all()


@app.post(
    "/api/products",
    response_model=ProductOut,
    status_code=201,
    dependencies=[Depends(require_bot)],
)
async def create_product(
    title: Annotated[str, Form(min_length=1, max_length=255)],
    image: Annotated[UploadFile, File()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    title = title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Пустое название")

    limit = settings.max_image_mb * 1024 * 1024
    data = await image.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=413, detail="Файл слишком большой")

    ext, content_type = await run_in_threadpool(detect_image, data)
    key = f"{uuid.uuid4().hex}.{ext}"
    await run_in_threadpool(storage.put_image, key, data, content_type)

    product = Product(title=title, image_key=key)
    session.add(product)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        # не оставляем «осиротевший» файл в S3, если запись в БД не удалась
        try:
            await run_in_threadpool(storage.remove_image, key)
        except Exception:
            logging.getLogger(__name__).exception("Failed to remove orphaned image %s", key)
        raise
    return product


@app.get("/api/media/{key}")
def media(key: str):
    if not KEY_RE.fullmatch(key):
        raise HTTPException(status_code=404)
    try:
        obj = storage.open_image(key)
    except S3Error:
        raise HTTPException(status_code=404)

    def stream():
        try:
            yield from obj.stream(64 * 1024)
        finally:
            obj.close()
            obj.release_conn()

    return StreamingResponse(
        stream(),
        media_type=obj.headers.get("Content-Type", "application/octet-stream"),
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
