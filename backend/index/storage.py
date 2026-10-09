"""Storage reader for ParsedDocument JSON artifacts in S3 / MinIO.

Normative sources:
- docs/mvp/03_data_model_and_contracts.md §3.4:
  Artifacts located at s3://plc-parsed/parsed/{work_id}/{expression_key}/{parse_id}.json.gz
- Rule: No imports of parse.* in backend/index/
"""

from __future__ import annotations

import gzip
import json
from typing import Any

import boto3
from botocore.client import Config
from django.conf import settings


def fetch_parsed_document(storage_uri: str) -> dict[str, Any]:
    """Download and decompress ParsedDocument JSON from S3."""
    if not storage_uri.startswith("s3://"):
        raise ValueError(f"Invalid storage URI '{storage_uri}'; expected s3:// prefix.")

    endpoint_url = getattr(settings, "S3_ENDPOINT_URL", "http://localhost:9000")
    access_key = getattr(settings, "S3_ACCESS_KEY_ID", "minioadmin")
    secret_key = getattr(settings, "S3_SECRET_ACCESS_KEY", "minioadmin")
    region = getattr(settings, "S3_REGION", "ap-south-1")

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(signature_version="s3v4"),
    )

    parts = storage_uri.replace("s3://", "").split("/", 1)
    bucket = parts[0]
    key = parts[1]

    resp = client.get_object(Bucket=bucket, Key=key)
    compressed_bytes = resp["Body"].read()
    raw_json_bytes = gzip.decompress(compressed_bytes)
    return json.loads(raw_json_bytes.decode("utf-8"))  # type: ignore[no-any-return]
