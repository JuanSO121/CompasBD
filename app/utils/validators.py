# ===== app/utils/validators.py =====

import re
from typing import List, Dict, Any, Optional
from email_validator import validate_email, EmailNotValidError

class AccessibleValidators:
    """Validadores con mensajes descriptivos para tecnologías asistivas"""
    
    @staticmethod
    def validate_email_accessible(email: str) -> Dict[str, Any]:
        """Validación de email con sugerencias accesibles - CORREGIDO"""
        try:
            validated_email = validate_email(email)
            return {
                "valid": True,
                "normalized_email": validated_email.email,
                "message": "Email válido",
                "suggestions": []
            }
        except EmailNotValidError as e:
            # Detectar errores comunes y sugerir correcciones
            suggestions = []
            
            if not email:
                suggestions.append("Ingrese su dirección de email")
                return {
                    "valid": False,
                    "normalized_email": None,
                    "message": "Email requerido",
                    "suggestions": suggestions
                }
            
            if "@" not in email:
                suggestions.append("Agregue el símbolo @ seguido del dominio (ejemplo: @gmail.com)")
            elif email.count("@") > 1:
                suggestions.append("Use solo un símbolo @ en su email")
            elif "@" in email and "." not in email.split("@")[-1]:
                suggestions.append("Agregue un punto en el dominio (ejemplo: gmail.com)")
            
            # Detectar dominios comunes mal escritos - CORREGIDO
            if "@" in email:
                try:
                    domain_part = email.split("@")[1].lower()
                    common_domains = {
                        "gmial": "gmail",
                        "gmai": "gmail", 
                        "yahooo": "yahoo",
                        "hotmial": "hotmail",
                        "outlok": "outlook"
                    }
                    
                    for typo, correct in common_domains.items():
                        if typo in domain_part:
                            corrected_domain = domain_part.replace(typo, correct)
                            suggestions.append(f"¿Quiso decir {email.split('@')[0]}@{corrected_domain}?")
                            break
                except IndexError:
                    # Si no hay parte después del @
                    suggestions.append("Agregue el dominio después del @ (ejemplo: @gmail.com)")
            
            return {
                "valid": False,
                "normalized_email": None,
                "message": f"Email inválido: {str(e)}",
                "suggestions": suggestions if suggestions else ["Verifique el formato del email"]
            }

    @staticmethod
    def validate_password_accessible(password: str) -> Dict[str, Any]:
        """Validación de contraseña con retroalimentación descriptiva"""
        if not password:
            return {
                "valid": False,
                "strength_score": 0,
                "strength_level": "muy débil",
                "strength_message": "Contraseña requerida",
                "errors": ["la contraseña es requerida"],
                "suggestions": ["Ingrese una contraseña segura"],
                "message": "La contraseña es requerida"
            }
        
        errors = []
        suggestions = []
        strength_score = 0
        
        # Longitud
        if len(password) < 8:
            errors.append("debe tener al menos 8 caracteres")
            suggestions.append("Agregue más caracteres para mayor seguridad")
        elif len(password) >= 8:
            strength_score += 1
            
        if len(password) >= 12:
            strength_score += 1
        
        # Mayúsculas
        if not re.search(r'[A-Z]', password):
            errors.append("debe incluir al menos una letra mayúscula")
            suggestions.append("Agregue una letra mayúscula (A-Z)")
        else:
            strength_score += 1
        
        # Minúsculas
        if not re.search(r'[a-z]', password):
            errors.append("debe incluir al menos una letra minúscula")
            suggestions.append("Agregue una letra minúscula (a-z)")
        else:
            strength_score += 1
        
        # Números
        if not re.search(r'\d', password):
            errors.append("debe incluir al menos un número")
            suggestions.append("Agregue un número (0-9)")
        else:
            strength_score += 1
        
        # Caracteres especiales
        special_chars = r'[!@#$%^&*(),.?":{}|<>]'
        if not re.search(special_chars, password):
            errors.append("debe incluir al menos un símbolo especial")
            suggestions.append("Agregue un símbolo especial (!@#$%^&* etc.)")
        else:
            strength_score += 1
        
        # Patrones comunes débiles
        weak_patterns = [
            (r'123', "Evite secuencias numéricas como 123"),
            (r'abc', "Evite secuencias alfabéticas como abc"),
            (r'password', "Evite usar la palabra 'password'"),
            (r'qwerty', "Evite patrones del teclado como qwerty"),
            (r'admin', "Evite palabras comunes como 'admin'")
        ]
        
        for pattern, suggestion in weak_patterns:
            if re.search(pattern, password.lower()):
                suggestions.append(suggestion)
                strength_score = max(0, strength_score - 1)
        
        # Determinar nivel de fortaleza
        if strength_score >= 5:
            strength_level = "muy fuerte"
            strength_message = "Excelente contraseña"
        elif strength_score >= 4:
            strength_level = "fuerte" 
            strength_message = "Buena contraseña"
        elif strength_score >= 3:
            strength_level = "moderada"
            strength_message = "Contraseña aceptable pero puede mejorar"
        elif strength_score >= 2:
            strength_level = "débil"
            strength_message = "Contraseña débil, necesita mejoras"
        else:
            strength_level = "muy débil"
            strength_message = "Contraseña muy débil, requiere cambios importantes"
        
        return {
            "valid": len(errors) == 0,
            "strength_score": strength_score,
            "strength_level": strength_level,
            "strength_message": strength_message,
            "errors": errors,
            "suggestions": suggestions if suggestions else ["La contraseña cumple con los requisitos"],
            "message": f"La contraseña {', '.join(errors)}" if errors else strength_message
        }
    
    @staticmethod
    def validate_phone_accessible(phone: str) -> Dict[str, Any]:
        """Validación de teléfono con formato accesible"""
        if not phone or not phone.strip():
            return {
                "valid": True, 
                "message": "Teléfono opcional",
                "suggestions": []
            }
        
        # Limpiar el número
        clean_phone = re.sub(r'[^\d+]', '', phone.strip())
        
        # Validaciones básicas
        if len(clean_phone) < 7:
            return {
                "valid": False,
                "message": "Número de teléfono muy corto",
                "suggestions": ["Incluya el código de área", "Use formato: +57 300 123 4567"]
            }
        
        if len(clean_phone) > 15:
            return {
                "valid": False,
                "message": "Número de teléfono muy largo",
                "suggestions": ["Verifique que no haya caracteres extra"]
            }
        
        # Verificar formato internacional
        if not clean_phone.startswith('+'):
            return {
                "valid": True,
                "normalized_phone": f"+57{clean_phone}" if len(clean_phone) == 10 else clean_phone,
                "message": "Número válido",
                "suggestions": ["Considere agregar código de país (+57 para Colombia)"]
            }
        
        return {
            "valid": True,
            "normalized_phone": clean_phone,
            "message": "Número de teléfono válido",
            "suggestions": []
        }
    
    @staticmethod
    def validate_name_accessible(name: str, field_name: str = "nombre") -> Dict[str, Any]:
        """Validación de nombre con retroalimentación accesible"""
        if not name or not name.strip():
            return {
                "valid": False,
                "message": f"El {field_name} es requerido",
                "suggestions": [f"Ingrese su {field_name}"]
            }
        
        clean_name = name.strip()
        
        if len(clean_name) < 2:
            return {
                "valid": False,
                "message": f"El {field_name} debe tener al menos 2 caracteres",
                "suggestions": [f"Ingrese su {field_name} completo"]
            }
        
        if len(clean_name) > 50:
            return {
                "valid": False,
                "message": f"El {field_name} no puede exceder 50 caracteres",
                "suggestions": ["Use una versión más corta del nombre"]
            }
        
        # Verificar caracteres válidos
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-\.\']+$', clean_name):
            return {
                "valid": False,
                "message": f"El {field_name} contiene caracteres no válidos",
                "suggestions": ["Use solo letras, espacios, guiones y apostrofes"]
            }
        
        return {
            "valid": True,
            "normalized_name": clean_name.title(),
            "message": f"{field_name.capitalize()} válido",
            "suggestions": []
        }

# ===== FIX: app/database/collections.py (agregar método faltante) =====

# Agregar este método a la clase UsersCollection:

    async def find_user_by_email_verification_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Buscar usuario por token de verificación de email"""
        try:
            collection = self.get_collection()
            user = await collection.find_one({
                "security.email_verification_token": token
            })
            return user
        except Exception as e:
            logger.error(f"❌ Error buscando usuario por token de verificación: {e}")
            return None

# ===== SCRIPT DE TESTING RÁPIDO =====
# Crear archivo: test_quick.py

import requests
import json

def test_backend():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Backend Accesible...")
    
    # 1. Health check
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        if response.status_code == 200:
            print("✅ Health check OK")
            data = response.json()
            print(f"   Headers accesibles: {bool(response.headers.get('X-Content-Accessible'))}")
        else:
            print(f"❌ Health check falló: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
        return
    
    # 2. Comandos de voz (sin auth)
    try:
        response = requests.get(f"{base_url}/api/v1/accessibility/voice-commands")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Comandos de voz OK - {data['data']['total_commands']} comandos")
        else:
            print(f"❌ Comandos de voz falló: {response.status_code}")
    except Exception as e:
        print(f"❌ Error en comandos de voz: {e}")
    
    # 3. Test registro (con datos válidos)
    try:
        register_data = {
            "email": "test@ejemplo.com",
            "password": "MiPassword123!",
            "confirm_password": "MiPassword123!",
            "first_name": "Usuario",
            "last_name": "Prueba",
            "visual_impairment_level": "low_vision",
            "screen_reader_user": True
        }
        
        response = requests.post(f"{base_url}/api/v1/auth/register", json=register_data)
        data = response.json()
        
        if data.get("success"):
            print("✅ Registro OK - Usuario creado")
        else:
            print(f"❌ Registro falló: {data.get('message', 'Error desconocido')}")
            if data.get("errors"):
                for error in data["errors"][:2]:  # Mostrar solo primeros 2 errores
                    print(f"   - {error['field']}: {error['message']}")
                    
    except Exception as e:
        print(f"❌ Error en registro: {e}")
    
    print("\n🎯 Testing completado!")

if __name__ == "__main__":
    test_backend()