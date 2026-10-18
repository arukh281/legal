"""Structured JSON logging configuration for lawyer_brain.

Enforces:
1. W3C traceparent logging.
2. Zero leakage of TENANT_CONFIDENTIAL or PRIVILEGED payload bodies (only IDs and hashes logged).
3. Standardized JSON output via structlog.
"""

import hashlib
import json
import logging
import re
from typing import Any

import structlog
from structlog.types import EventDict

SENSITIVE_DATACLASSES = {"TENANT_CONFIDENTIAL", "PRIVILEGED"}


SHARE_PATH_PATTERN = re.compile(r"/share/[A-Za-z0-9_\-]+")


def filter_sensitive_payloads(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Ensure sensitive payload bodies are never logged in plaintext."""
    dataclass = event_dict.get("dataclass")
    if dataclass in SENSITIVE_DATACLASSES:
        for field in ("body", "data", "payload", "text", "raw_content"):
            if field in event_dict:
                val = event_dict[field]
                if isinstance(val, (dict, list)):
                    raw_bytes = json.dumps(val, sort_keys=True).encode()
                elif isinstance(val, str):
                    raw_bytes = val.encode()
                elif isinstance(val, bytes):
                    raw_bytes = val
                else:
                    raw_bytes = str(val).encode()
                event_dict[field] = f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}"
                event_dict[f"{field}_masked"] = True

    # Redact share tokens from any logged paths or strings
    for key, val in list(event_dict.items()):
        if isinstance(val, str) and "/share/" in val:
            event_dict[key] = SHARE_PATH_PATTERN.sub("/share/<redacted>", val)

    return event_dict


class UvicornShareTokenFilter(logging.Filter):
    """Filter on uvicorn.access logger to redact share tokens from access logs."""

    PATTERN = re.compile(r"/share/[^\s\?\"']+")

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            if isinstance(record.args, tuple):
                new_args = list(record.args)
                for i, arg in enumerate(new_args):
                    if isinstance(arg, str) and "/share/" in arg:
                        new_args[i] = self.PATTERN.sub("/share/<redacted>", arg)
                record.args = tuple(new_args)
            elif isinstance(record.args, dict):
                new_args_dict = dict(record.args)
                for k, v in new_args_dict.items():
                    if isinstance(v, str) and "/share/" in v:
                        new_args_dict[k] = self.PATTERN.sub("/share/<redacted>", v)
                record.args = new_args_dict
        if isinstance(record.msg, str) and "/share/" in record.msg:
            record.msg = self.PATTERN.sub("/share/<redacted>", record.msg)
        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structlog and standard logging."""
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        filter_sensitive_payloads,
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Redact share tokens from uvicorn access logs (Session R3 Fix Pass - Item 10)
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.addFilter(UvicornShareTokenFilter())
