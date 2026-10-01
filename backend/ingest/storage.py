"""Content-Addressed Storage (CAS) for raw blobs in S3/MinIO.

Normative source:
- docs/mvp/04_stack_and_infra.md §2.9:
  S3 ap-south-1 (MinIO standing in for S3 in local development).
  Bucket: raw/ (Object Lock governance mode, content-addressed sha256).
- docs/mvp/03_data_model_and_contracts.md §3.2 (plc.raw_blob)
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

import boto3
from botocore.client import Config
from django.conf import settings
from django.db import transaction

from ingest.models import RawBlob


class BlobStorage:
    """Content-addressed blob storage backed by S3 / MinIO."""

    def __init__(
        self,
        *,
        endpoint_url: str | None = None,
        bucket_name: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str | None = None,
    ) -> None:
        self.endpoint_url = endpoint_url or getattr(
            settings, "S3_ENDPOINT_URL", "http://localhost:9000"
        )
        self.bucket_name = bucket_name or getattr(settings, "S3_RAW_BUCKET", "plc-raw")
        self.access_key = access_key or getattr(settings, "S3_ACCESS_KEY_ID", "minioadmin")
        self.secret_key = secret_key or getattr(settings, "S3_SECRET_ACCESS_KEY", "minioadmin")
        self.region = region or getattr(settings, "S3_REGION", "ap-south-1")

        self._s3_client: Any = None

    def _get_client(self) -> Any:
        if self._s3_client is None:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(signature_version="s3v4"),
            )
            self._ensure_bucket()
        return self._s3_client

    def _ensure_bucket(self) -> None:
        """Create the raw bucket if it does not exist (primarily for MinIO dev)."""
        try:
            self._s3_client.head_bucket(Bucket=self.bucket_name)
        except Exception:
            try:
                self._s3_client.create_bucket(Bucket=self.bucket_name)
            except Exception:
                pass

    def compute_raw_id(self, data: bytes) -> str:
        """Compute sha256:<64-char-lowercase-hex> raw_id."""
        hex_digest = hashlib.sha256(data).hexdigest()
        return f"sha256:{hex_digest}"

    def build_s3_key(self, raw_id: str, content_type: str = "application/pdf") -> str:
        """Build hierarchical content-addressed S3 object key."""
        hex_hash = raw_id.split(":", 1)[1]
        ext = ".pdf" if "pdf" in content_type.lower() else ".bin"
        return f"raw/sha256/{hex_hash[:2]}/{hex_hash[2:4]}/{hex_hash}{ext}"

    def store_blob(
        self,
        data: bytes,
        *,
        content_type: str = "application/pdf",
        first_seen_at: datetime | None = None,
    ) -> tuple[str, str, int]:
        """Store bytes content-addressed in S3 and record in plc.raw_blob.

        Returns (raw_id, storage_uri, byte_size).
        If raw_id is already present, avoids duplicate S3 upload and DB insertion.
        """
        raw_id = self.compute_raw_id(data)
        byte_size = len(data)
        first_seen = first_seen_at or datetime.now(UTC)
        s3_key = self.build_s3_key(raw_id, content_type)
        storage_uri = f"s3://{self.bucket_name}/{s3_key}"

        # 1. Check if RawBlob already exists in DB
        existing = RawBlob.objects.filter(raw_id=raw_id).first()
        if existing is not None:
            return existing.raw_id, existing.storage_uri, existing.byte_size

        # 2. Upload to S3/MinIO
        client = self._get_client()
        client.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=data,
            ContentType=content_type,
        )

        # 3. Insert into plc.raw_blob inside transaction
        with transaction.atomic():
            RawBlob.objects.get_or_create(
                raw_id=raw_id,
                defaults={
                    "storage_uri": storage_uri,
                    "byte_size": byte_size,
                    "content_type": content_type,
                    "first_seen_at": first_seen,
                },
            )

        return raw_id, storage_uri, byte_size

    def get_blob(self, raw_id: str, content_type: str = "application/pdf") -> bytes:
        """Retrieve blob bytes from S3 by raw_id."""
        s3_key = self.build_s3_key(raw_id, content_type)
        client = self._get_client()
        resp = client.get_object(Bucket=self.bucket_name, Key=s3_key)
        return resp["Body"].read()  # type: ignore[no-any-return]
