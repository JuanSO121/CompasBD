# ===== app/services/verification_service.py =====
import secrets
import string
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.database.collections import users_collection
from app.services.email_service import email_service
import logging

logger = logging.getLogger(__name__)

class VerificationService:
    """Servicio de verificación accesible con códigos de 6 dígitos"""
    
    CODE_LENGTH = 6
    CODE_EXPIRATION_MINUTES = 15
    MAX_ATTEMPTS = 5
    
    @staticmethod
    def generate_verification_code() -> str:
        """Generar código numérico de 6 dígitos"""
        return ''.join(secrets.choice(string.digits) for _ in range(VerificationService.CODE_LENGTH))
    
    @staticmethod
    async def create_verification_code(user_id: str) -> Optional[Dict[str, Any]]:
        """Crear y guardar código de verificación"""
        try:
            code = VerificationService.generate_verification_code()
            expires_at = datetime.utcnow() + timedelta(minutes=VerificationService.CODE_EXPIRATION_MINUTES)
            
            verification_data = {
                "code": code,
                "expires_at": expires_at,
                "attempts": 0,
                "created_at": datetime.utcnow()
            }
            
            # Guardar en el usuario
            success = await users_collection.update_user(
                user_id,
                {"security.email_verification_code": verification_data}
            )
            
            if success:
                return verification_data
            return None
            
        except Exception as e:
            logger.error(f"❌ Error creando código de verificación: {e}")
            return None
    
    @staticmethod
    async def send_verification_code(email: str, user_name: str = "") -> bool:
        """Enviar código de verificación por email"""
        try:
            # Obtener usuario
            user = await users_collection.find_user_by_email(email)
            if not user:
                return False
            
            # Crear nuevo código
            verification_data = await VerificationService.create_verification_code(str(user["_id"]))
            if not verification_data:
                return False
            
            code = verification_data["code"]
            
            # Enviar email con código
            return await email_service.send_verification_code_email(
                email=email,
                code=code,
                user_name=user_name,
                expires_minutes=VerificationService.CODE_EXPIRATION_MINUTES
            )
            
        except Exception as e:
            logger.error(f"❌ Error enviando código de verificación: {e}")
            return False
    
    @staticmethod
    async def verify_code(email: str, code: str) -> Dict[str, Any]:
        """Verificar código de verificación"""
        try:
            # Buscar usuario
            user = await users_collection.find_user_by_email(email)
            if not user:
                return {
                    "success": False,
                    "message": "Usuario no encontrado",
                    "error_type": "user_not_found"
                }
            
            # Obtener datos de verificación
            verification_data = user.get("security", {}).get("email_verification_code")
            if not verification_data:
                return {
                    "success": False,
                    "message": "No hay código de verificación activo. Solicite uno nuevo.",
                    "error_type": "no_code"
                }
            
            # Verificar expiración
            expires_at = verification_data.get("expires_at")
            if datetime.utcnow() > expires_at:
                return {
                    "success": False,
                    "message": "El código ha expirado. Solicite uno nuevo.",
                    "error_type": "expired"
                }
            
            # Verificar intentos
            attempts = verification_data.get("attempts", 0)
            if attempts >= VerificationService.MAX_ATTEMPTS:
                return {
                    "success": False,
                    "message": "Demasiados intentos fallidos. Solicite un nuevo código.",
                    "error_type": "max_attempts"
                }
            
            # Verificar código
            stored_code = verification_data.get("code")
            if code != stored_code:
                # Incrementar intentos
                await users_collection.update_user(
                    str(user["_id"]),
                    {"security.email_verification_code.attempts": attempts + 1}
                )
                
                remaining_attempts = VerificationService.MAX_ATTEMPTS - (attempts + 1)
                return {
                    "success": False,
                    "message": f"Código incorrecto. {remaining_attempts} intentos restantes.",
                    "error_type": "invalid_code",
                    "remaining_attempts": remaining_attempts
                }
            
            # Código correcto - verificar cuenta
            await users_collection.update_user(
                str(user["_id"]),
                {
                    "is_verified": True,
                    "security.email_verification_code": None,
                    "security.email_verified_at": datetime.utcnow()
                }
            )
            
            return {
                "success": True,
                "message": "Email verificado exitosamente",
                "user_id": str(user["_id"])
            }
            
        except Exception as e:
            logger.error(f"❌ Error verificando código: {e}")
            return {
                "success": False,
                "message": "Error interno verificando el código",
                "error_type": "server_error"
            }

verification_service = VerificationService()