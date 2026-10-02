"""Storage for ParsedDocument JSON artifacts in S3 / MinIO.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.4:
  Written gzip-compressed to S3 at parsed/{work_id}/{expression_key}/{parse_id}.json.gz
- Directive #5: Upload to S3 first, then commit DB transaction.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from typing import Any

import boto3
from botocore.client import Config
from django.conf import settings


class ParsedDocStorage:
    """Storage client for ParsedDocument JSON artifacts."""

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
        self.bucket_name = bucket_name or getattr(settings, "S3_PARSED_BUCKET", "plc-parsed")
        self.access_key = access_key or getattr(settings, "S3_ACCESS_KEY_ID", "minioadmin")
        self.secret_key = secret_key or getattr(settings, "S3_SECRET_ACCESS_KEY", "minioadmin")
        self.region = region or getattr(settings, "S3_REGION", "ap-south-1")
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(signature_version="s3v4"),
            )
            self._ensure_bucket()
        return self._client

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self.bucket_name)
        except Exception:
            try:
                self._client.create_bucket(Bucket=self.bucket_name)
            except Exception:
                pass

    def build_s3_key(self, work_id: str, expression_key: str, parse_id: str) -> str:
        return f"parsed/{work_id}/{expression_key}/{parse_id}.json.gz"

    def upload_parsed_document(
        self,
        parsed_doc: dict[str, Any],
        *,
        work_id: str,
        expression_key: str,
        parse_id: str,
    ) -> tuple[str, str]:
        """Serialize, sha256 hash, gzip, and upload ParsedDocument to S3.

        Returns (storage_uri, sha256_hex).
        """
        raw_json_bytes = json.dumps(parsed_doc, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        sha256_hex = hashlib.sha256(raw_json_bytes).hexdigest()
        compressed_bytes = gzip.compress(raw_json_bytes)

        s3_key = self.build_s3_key(work_id, expression_key, parse_id)
        storage_uri = f"s3://{self.bucket_name}/{s3_key}"

        client = self._get_client()
        client.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=compressed_bytes,
            ContentType="application/json",
            ContentEncoding="gzip",
        )
        return storage_uri, sha256_hex

    def get_parsed_document(self, storage_uri: str) -> dict[str, Any]:
        """Download and decompress ParsedDocument JSON from S3."""
        # storage_uri is s3://bucket/key
        parts = storage_uri.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        client = self._get_client()
        resp = client.get_object(Bucket=bucket, Key=key)
        compressed_bytes = resp["Body"].read()
        raw_json_bytes = gzip.decompress(compressed_bytes)
        return json.loads(raw_json_bytes.decode("utf-8"))  # type: ignore[no-any-return]

    fetch_parsed_document = get_parsed_document
