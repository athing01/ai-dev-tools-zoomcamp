import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def anyio_backend():
    return "asyncio"
