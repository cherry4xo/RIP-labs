import json
import os
from typing import IO, Annotated, Optional
from fastapi import Depends
from minio import Minio
from minio.error import S3Error

from app.core import settings
from app.interfaces import AbstractFileStorage


class MinioFileStorage(AbstractFileStorage):
    def __init__(self) -> None:
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        try:
            found = self.client.bucket_exists(self.bucket_name)
            if not found:
                self.client.make_bucket(self.bucket_name)
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": "s3:GetObject",
                            "Resource": f"arn:aws:s3:::{self.bucket_name}/*",
                        },
                    ],
                }
                self.client.set_bucket_policy(self.bucket_name, json.dumps(policy))
                print(f"Bucket '{self.bucket_name}' created and set to public read.")
        except S3Error as e:
            print(f"Error checking or creating bucket: {e}")
            raise

    def save(self, file: IO, filename: str, content_type: str) -> str:
        file_content = file.read()
        file_size = len(file_content)

        from io import BytesIO
        file_like_object = BytesIO(file_content)

        try:
            self.client.put_object(
                self.bucket_name,
                filename,
                file_like_object,
                length=file_size,
                content_type=content_type
            )
            return f"http://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{filename}"
        except S3Error as e:
            print(f"Error uploading to MinIO: {e}")
            raise

    def delete(self, file_url: str) -> None:
        filename = file_url.split('/')[-1]
        try:
            self.client.remove_object(self.bucket_name, filename)
        except S3Error as e:
            print(f"Error deleting from MinIO: {e}")


_storage_instance: Optional[MinioFileStorage] = None

def get_file_storage() -> AbstractFileStorage:
    """
    Возвращает синглтон-экземпляр файлового хранилища,
    создавая его при первом вызове.
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = MinioFileStorage()
    return _storage_instance


FileStorageDep = Annotated[AbstractFileStorage, Depends(get_file_storage)]