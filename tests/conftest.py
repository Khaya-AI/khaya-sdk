import pytest

from khaya import KhayaClient
from khaya.config import Settings


@pytest.fixture
def api_key() -> str:
    return "test-api-key"


@pytest.fixture
def khaya_client(api_key: str) -> KhayaClient:
    """KhayaClient configured for unit tests (no retries, no live API)."""
    config = Settings(api_key=api_key, retry_attempts=1)
    return KhayaClient(api_key=api_key, config=config)
