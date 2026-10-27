import io

from minio import Minio
from minio.error import S3Error

from .config import settings

client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)


def ensure_bucket() -> None:
    if not client.bucket_exists(settings.minio_bucket):
        try:
            client.make_bucket(settings.minio_bucket)
        except S3Error as exc:
            if exc.code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                raise


def put_image(key: str, data: bytes, content_type: str) -> None:
    client.put_object(
        settings.minio_bucket, key, io.BytesIO(data), len(data), content_type=content_type
    )


def remove_image(key: str) -> None:
    client.remove_object(settings.minio_bucket, key)


def open_image(key: str):
    return client.get_object(settings.minio_bucket, key)
