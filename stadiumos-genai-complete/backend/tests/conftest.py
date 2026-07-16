import os
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure the app package is importable when pytest is run from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Force a clean, key-less environment for deterministic fallback-mode tests
# unless a test explicitly monkeypatches the AI layer.
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
os.environ.setdefault("RATE_LIMIT_REQUESTS", "1000")  # tests shouldn't trip rate limits by default

from app.main import app  # noqa: E402


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
