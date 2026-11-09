import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from .config import settings

logger = logging.getLogger("labspoc.storage")

class StorageAdapter(ABC):
    """Abstract interface for LabSPOC AI persistent storage backends."""

    @abstractmethod
    def save(self, path_key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Saves data bytes under path_key and returns relative or public access path."""
        pass

    @abstractmethod
    def load(self, path_key: str) -> Optional[bytes]:
        """Loads and returns data bytes for path_key, or None if not found."""
        pass

    @abstractmethod
    def delete(self, path_key: str) -> bool:
        """Deletes file at path_key. Returns True if deleted or did not exist."""
        pass

    @abstractmethod
    def exists(self, path_key: str) -> bool:
        """Returns True if path_key exists in storage."""
        pass

    @abstractmethod
    def get_url(self, path_key: str) -> str:
        """Returns public or relative serving URL for path_key."""
        pass

    @abstractmethod
    def health_check(self) -> dict:
        """Performs a readiness/connectivity test for the storage backend."""
        pass


class LocalStorageAdapter(StorageAdapter):
    """Local filesystem storage adapter with path traversal prevention."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "media").mkdir(parents=True, exist_ok=True)

    def _resolve(self, path_key: str) -> Path:
        clean_key = path_key.lstrip("/\\")
        target = (self.base_dir / clean_key).resolve()
        if not str(target).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected: {path_key}")
        return target

    def save(self, path_key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        target = self._resolve(path_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return path_key

    def load(self, path_key: str) -> Optional[bytes]:
        try:
            target = self._resolve(path_key)
            if target.is_file():
                return target.read_bytes()
            return None
        except Exception as e:
            logger.warning(f"Failed to load {path_key}: {e}")
            return None

    def delete(self, path_key: str) -> bool:
        try:
            target = self._resolve(path_key)
            if target.is_file():
                target.unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to delete {path_key}: {e}")
            return False

    def exists(self, path_key: str) -> bool:
        try:
            target = self._resolve(path_key)
            return target.is_file()
        except Exception:
            return False

    def get_url(self, path_key: str) -> str:
        clean = path_key.replace("\\", "/").lstrip("/")
        if clean.startswith("media/"):
            return f"/{clean}"
        return f"/uploads/{clean}"

    def health_check(self) -> dict:
        try:
            test_file = self.base_dir / ".storage_health_test"
            test_file.write_bytes(b"health_ok")
            content = test_file.read_bytes()
            test_file.unlink(missing_ok=True)
            if content == b"health_ok":
                return {"status": "ok", "backend": "local", "path": str(self.base_dir), "writable": True}
            return {"status": "error", "backend": "local", "writable": False, "error": "readback_failed"}
        except Exception as e:
            return {"status": "error", "backend": "local", "writable": False, "error": str(e)}


class S3StorageAdapter(StorageAdapter):
    """Production S3-compatible object storage adapter (AWS S3, MinIO, Cloudflare R2)."""

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
        public_url_prefix: Optional[str] = None
    ):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.region_name = region_name
        self.public_url_prefix = public_url_prefix.rstrip("/") if public_url_prefix else None
        
        try:
            import boto3
            from botocore.config import Config
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url if self.endpoint_url else None,
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                region_name=self.region_name,
                config=Config(signature_version="s3v4")
            )
            self._boto3_available = True
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self._client = None
            self._boto3_available = False

    def save(self, path_key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        clean_key = path_key.lstrip("/\\").replace("\\", "/")
        if not self._client:
            raise RuntimeError("S3 client not initialized")
        self._client.put_object(
            Bucket=self.bucket_name,
            Key=clean_key,
            Body=data,
            ContentType=content_type
        )
        return clean_key

    def load(self, path_key: str) -> Optional[bytes]:
        clean_key = path_key.lstrip("/\\").replace("\\", "/")
        if not self._client:
            return None
        try:
            response = self._client.get_object(Bucket=self.bucket_name, Key=clean_key)
            return response["Body"].read()
        except Exception as e:
            logger.warning(f"S3 get_object failed for {clean_key}: {e}")
            return None

    def delete(self, path_key: str) -> bool:
        clean_key = path_key.lstrip("/\\").replace("\\", "/")
        if not self._client:
            return False
        try:
            self._client.delete_object(Bucket=self.bucket_name, Key=clean_key)
            return True
        except Exception as e:
            logger.error(f"S3 delete_object failed for {clean_key}: {e}")
            return False

    def exists(self, path_key: str) -> bool:
        clean_key = path_key.lstrip("/\\").replace("\\", "/")
        if not self._client:
            return False
        try:
            self._client.head_object(Bucket=self.bucket_name, Key=clean_key)
            return True
        except Exception:
            return False

    def get_url(self, path_key: str) -> str:
        clean_key = path_key.lstrip("/\\").replace("\\", "/")
        if self.public_url_prefix:
            return f"{self.public_url_prefix}/{clean_key}"
        if self.endpoint_url:
            return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{clean_key}"
        return f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{clean_key}"

    def health_check(self) -> dict:
        if not self._boto3_available or not self._client:
            return {"status": "error", "backend": "s3", "error": "boto3_client_unavailable"}
        try:
            self._client.head_bucket(Bucket=self.bucket_name)
            return {"status": "ok", "backend": "s3", "bucket": self.bucket_name, "endpoint": self.endpoint_url or "aws-default"}
        except Exception as e:
            return {"status": "error", "backend": "s3", "bucket": self.bucket_name, "error": str(e)}


_storage_singleton: Optional[StorageAdapter] = None

def get_storage() -> StorageAdapter:
    """Returns singleton StorageAdapter configured from application settings."""
    global _storage_singleton
    if _storage_singleton is not None:
        return _storage_singleton

    if settings.storage_backend.lower() == "s3" and settings.s3_bucket_name:
        _storage_singleton = S3StorageAdapter(
            bucket_name=settings.s3_bucket_name,
            endpoint_url=settings.s3_endpoint_url or None,
            access_key_id=settings.s3_access_key_id or None,
            secret_access_key=settings.s3_secret_access_key or None,
            region_name=settings.s3_region,
            public_url_prefix=settings.s3_public_url or None
        )
    else:
        _storage_singleton = LocalStorageAdapter(base_dir=settings.upload_dir)

    return _storage_singleton
