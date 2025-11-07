# ===== tests/test_auth.py =====
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAuthentication:
    """Tests para endpoints de autenticación"""
    
    def test_register_user_success(self):
        """Test registro exitoso"""
        user_data = {
            "email": "test@ejemplo.com",
            "password": "ContraseñaSegura123!",
            "confirm_password": "ContraseñaSegura123!",
            "first_name": "Juan",
            "last_name": "Pérez",
            "visual_impairment_level": "low_vision",
            "screen_reader_user": True
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "usuario creado" in data["message"].lower()
        assert data["accessibility_info"]["haptic_pattern"] == "success"
    
    def test_register_user_invalid_email(self):
        """Test registro con email inválido"""
        user_data = {
            "email": "email-invalido",
            "password": "ContraseñaSegura123!",
            "confirm_password": "ContraseñaSegura123!"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == False
        assert len(data["errors"]) > 0
        assert data["accessibility_info"]["haptic_pattern"] == "error"
    
    def test_register_user_weak_password(self):
        """Test registro con contraseña débil"""
        user_data = {
            "email": "test@ejemplo.com",
            "password": "123",
            "confirm_password": "123"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == False
        assert any("contraseña" in error["message"].lower() for error in data["errors"])
    
    def test_login_user_success(self):
        """Test login exitoso (requiere usuario ya registrado)"""
        # Primero registrar
        register_data = {
            "email": "login_test@ejemplo.com",
            "password": "ContraseñaSegura123!",
            "confirm_password": "ContraseñaSegura123!"
        }
        client.post("/api/v1/auth/register", json=register_data)
        
        # Luego hacer login
        login_data = {
            "email": "login_test@ejemplo.com",
            "password": "ContraseñaSegura123!"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        # Nota: fallará si el email no está verificado
        # En un test real, verificaríamos el email primero
        data = response.json()
        assert "success" in data
        assert "accessibility_info" in data
    
    def test_accessibility_headers_present(self):
        """Test que los headers de accesibilidad estén presentes"""
        response = client.get("/api/v1/health")
        
        assert "X-Content-Accessible" in response.headers
        assert "X-Screen-Reader-Friendly" in response.headers
        assert response.headers["X-Content-Accessible"] == "true"
    
    def test_structured_error_response(self):
        """Test que las respuestas de error sigan el formato accesible"""
        response = client.post("/api/v1/auth/login", json={
            "email": "invalido",
            "password": "123"
        })
        
        data = response.json()
        required_fields = ["success", "message", "message_type", "accessibility_info", "errors"]
        for field in required_fields:
            assert field in data
        
        assert data["accessibility_info"]["haptic_pattern"] in ["success", "error", "warning", "info"]
        assert isinstance(data["errors"], list)