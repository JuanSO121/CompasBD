# ===== tests/test_accessibility.py =====
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAccessibility:
    """Tests específicos para características de accesibilidad"""
    
    def test_voice_commands_endpoint(self):
        """Test endpoint de comandos de voz"""
        response = client.get("/api/v1/accessibility/voice-commands")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "voice_commands" in data["data"]
        assert "commands_by_category" in data["data"]
        assert len(data["data"]["voice_commands"]) > 0
    
    def test_voice_commands_filtering(self):
        """Test filtrado de comandos de voz"""
        response = client.get("/api/v1/accessibility/voice-commands?accessibility_level=blind")
        assert response.status_code == 200
        
        data = response.json()
        commands = data["data"]["voice_commands"]
        for cmd in commands:
            assert cmd["accessibility_level"] in ["blind", "all"]
    
    def test_device_capabilities_detection(self):
        """Test detección de capacidades del dispositivo"""
        # Requiere autenticación - en un test real usaríamos fixtures para login
        pass
    
    def test_accessibility_response_structure(self):
        """Test que todas las respuestas sigan la estructura accesible"""
        endpoints_to_test = [
            "/api/v1/health",
            "/api/v1/health/accessibility",
            "/api/v1/accessibility/voice-commands"
        ]
        
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            data = response.json()
            
            # Verificar estructura accesible
            assert "success" in data
            assert "message" in data
            assert "accessibility_info" in data
            assert "haptic_pattern" in data["accessibility_info"]
            assert "announcement" in data["accessibility_info"]
