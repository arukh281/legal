"""Evaluation harness root package."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path when running scripts from repo root
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.local")
