# ===== test_backend.py =====
"""
Script para probar el backend de accesibilidad
Ejecutar: python test_backend.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    """Imprimir respuesta formateada"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    try:
        data = response.json()
        print(f"Response:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")

def test_health_check():
    """Test 1: Health Check"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health")
        print_response("Health Check", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        return False

def test_accessibility_health():
    """Test 2: Accessibility Health Check"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health/accessibility")
        print_response("Accessibility Health Check", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error en accessibility health: {e}")
        return False

def test_voice_commands():
    """Test 3: Comandos de Voz"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/accessibility/voice-commands")
        print_response("Voice Commands", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error en voice commands: {e}")
        return False

def test_register_invalid():
    """Test 4: Registro con datos inválidos (debe fallar con mensajes descriptivos)"""
    try:
        data = {
            "email": "test@ejemplo.com",
            "password": "Weak",  # Contraseña débil
            "confirm_password": "Weak",
            "first_name": "Usuario",
            "last_name": "Prueba"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=data)
        print_response("Register Invalid (Should Fail)", response)
        
        # Debe fallar con código 422 o 400
        return response.status_code in [400, 422]
    except Exception as e:
        print(f"❌ Error en register invalid: {e}")
        return False

def test_register_valid():
    """Test 5: Registro con datos válidos"""
    try:
        # Usar timestamp para evitar conflictos
        timestamp = int(datetime.now().timestamp())
        
        data = {
            "email": f"test_{timestamp}@ejemplo.com",
            "password": "TestPassword123!",
            "confirm_password": "TestPassword123!",
            "first_name": "Usuario",
            "last_name": "Prueba",
            "visual_impairment_level": "low_vision",
            "screen_reader_user": True
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=data)
        print_response("Register Valid", response)
        
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"❌ Error en register valid: {e}")
        return False

def test_login_invalid():
    """Test 6: Login con credenciales inválidas (debe fallar)"""
    try:
        data = {
            "email": "noexiste@ejemplo.com",
            "password": "WrongPassword123!"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=data)
        print_response("Login Invalid (Should Fail)", response)
        
        # Debe retornar error pero con 200 (success: false en el body)
        return response.status_code in [200, 401]
    except Exception as e:
        print(f"❌ Error en login invalid: {e}")
        return False

def test_root():
    """Test 7: Endpoint Raíz"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print_response("Root Endpoint", response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error en root: {e}")
        return False

def run_all_tests():
    """Ejecutar todas las pruebas"""
    print("\n" + "="*60)
    print("🚀 INICIANDO PRUEBAS DEL BACKEND ACCESIBLE")
    print("="*60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Accessibility Health", test_accessibility_health),
        ("Voice Commands", test_voice_commands),
        ("Register Invalid", test_register_invalid),
        ("Register Valid", test_register_valid),
        ("Login Invalid", test_login_invalid),
        ("Root Endpoint", test_root)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error ejecutando {name}: {e}")
            results.append((name, False))
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} pruebas pasadas ({(passed/total)*100:.1f}%)")
    print(f"{'='*60}\n")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Pruebas interrumpidas por el usuario")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        exit(1)