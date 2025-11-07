# ===== tests/conftest.py =====
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def async_client():
    """Async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def test_user_data():
    """Datos de usuario para testing"""
    return {
        "email": "testuser@ejemplo.com",
        "password": "ContraseñaSegura123!",
        "confirm_password": "ContraseñaSegura123!",
        "first_name": "Usuario",
        "last_name": "Prueba",
        "visual_impairment_level": "blind",
        "screen_reader_user": True
    }
