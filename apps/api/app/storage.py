from functools import lru_cache
from pathlib import Path
from typing import BinaryIO, Protocol

from minio import Minio
from minio.error import S3Error

from app.config import get_settings


class ObjectStoreError(RuntimeError):
    pass


class ObjectStore(Protocol):
    def put(self, key: str, stream: BinaryIO, length: int, content_type: str) -> None: ...
    def get(self, key: str) -> bytes: ...


class LocalObjectStore:
    def __init__(self, root: str):
        self.root = Path(root)

    def put(self, key: str, stream: BinaryIO, length: int, content_type: str) -> None:
        target = self.root / key
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as output:
            remaining = length
            while remaining:
                chunk = stream.read(min(1_048_576, remaining))
                if not chunk:
                    raise ObjectStoreError("Upload stream ended before expected size")
                output.write(chunk)
                remaining -= len(chunk)

    def get(self, key: str) -> bytes:
        target = (self.root / key).resolve()
        if self.root.resolve() not in target.parents:
            raise ObjectStoreError("Invalid object key")
        try:
            return target.read_bytes()
        except OSError as error:
            raise ObjectStoreError("Object storage is unavailable") from error


class MinioObjectStore:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str):
        secure = endpoint.startswith("https://")
        host = endpoint.removeprefix("https://").removeprefix("http://")
        self.client = Minio(host, access_key=access_key, secret_key=secret_key, secure=secure)
        self.bucket = bucket

    def put(self, key: str, stream: BinaryIO, length: int, content_type: str) -> None:
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
            self.client.put_object(self.bucket, key, stream, length, content_type=content_type)
        except S3Error as error:
            raise ObjectStoreError("Object storage is unavailable") from error

    def get(self, key: str) -> bytes:
        try:
            response = self.client.get_object(self.bucket, key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except S3Error as error:
            raise ObjectStoreError("Object storage is unavailable") from error


@lru_cache
def get_object_store() -> ObjectStore:
    settings = get_settings()
    if settings.object_storage_access_key and settings.object_storage_secret_key:
        return MinioObjectStore(
            settings.object_storage_endpoint,
            settings.object_storage_access_key,
            settings.object_storage_secret_key,
            settings.object_storage_bucket,
        )
    return LocalObjectStore(settings.local_storage_dir)
