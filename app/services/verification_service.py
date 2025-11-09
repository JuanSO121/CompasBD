# ===== app/services/verification_service.py =====
from http.client import HTTPException
import secrets
import string
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from requests import Request
from app.database.collections import users_collection
from app.middleware import security
from app.services import auth_service
from app.services.email_service import EmailService, email_service
from app.utils.helpers import AccessibleHelpers
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


# ===== app/services/email_service.py (ACTUALIZAR) =====
# Agregar este método a la clase EmailService

@staticmethod
async def send_verification_code_email(
    email: str, 
    code: str, 
    user_name: str = "",
    expires_minutes: int = 15
) -> bool:
    """Enviar email con código de verificación accesible"""
    
    subject = "Código de Verificación - App Accesible"
    
    # Formatear código para mejor lectura por TTS (espaciado)
    spaced_code = ' '.join(code)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{subject}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #2563eb; color: white; padding: 30px 20px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ padding: 30px 20px; background: white; }}
            .code-container {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 30px; 
                text-align: center; 
                border-radius: 16px;
                margin: 30px 0;
                box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            }}
            .verification-code {{ 
                font-size: 48px; 
                font-weight: bold; 
                color: white;
                letter-spacing: 12px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
                margin: 20px 0;
                font-family: 'Courier New', monospace;
            }}
            .code-label {{
                color: white;
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 10px;
            }}
            .accessible-info {{ 
                background-color: #f0f9ff; 
                padding: 20px; 
                margin: 20px 0; 
                border-left: 4px solid #2563eb;
                border-radius: 8px;
            }}
            .info-box {{
                background-color: #fef3c7;
                padding: 15px;
                border-left: 4px solid #f59e0b;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #666;
                font-size: 14px;
            }}
            ul {{
                list-style: none;
                padding-left: 0;
            }}
            li {{
                padding: 8px 0;
                display: flex;
                align-items: center;
            }}
            li:before {{
                content: "✓";
                color: #16a34a;
                font-weight: bold;
                font-size: 18px;
                margin-right: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header" role="banner">
                <h1>🔐 Código de Verificación</h1>
            </div>
            
            <div class="content" role="main">
                <p>Hola{"" if not user_name else f" {user_name}"},</p>
                
                <p style="font-size: 17px;">Tu código de verificación para activar tu cuenta es:</p>
                
                <div class="code-container" role="region" aria-label="Código de verificación">
                    <div class="code-label">TU CÓDIGO ES:</div>
                    <div class="verification-code" aria-label="Código: {spaced_code}">
                        {code}
                    </div>
                    <p style="color: white; margin-top: 15px; font-size: 14px;">
                        ⏱️ Válido por {expires_minutes} minutos
                    </p>
                </div>
                
                <div class="accessible-info" role="complementary">
                    <h3 style="margin-top: 0; color: #2563eb;">📱 Para usuarios de lectores de pantalla:</h3>
                    <p style="font-size: 16px;">
                        Ingresa este código en la aplicación para verificar tu cuenta.
                        El código es: <strong style="font-size: 18px; letter-spacing: 4px;">{spaced_code}</strong>
                    </p>
                    <p style="font-size: 15px; color: #666;">
                        Puedes copiar y pegar el código, o ingresarlo manualmente dígito por dígito.
                    </p>
                </div>
                
                <div class="info-box">
                    <h3 style="margin-top: 0; color: #f59e0b;">⚠️ Importante:</h3>
                    <ul>
                        <li>No compartas este código con nadie</li>
                        <li>El código expira en {expires_minutes} minutos</li>
                        <li>Si no solicitaste este código, ignora este email</li>
                        <li>Tienes 5 intentos para ingresar el código correcto</li>
                    </ul>
                </div>
                
                <p style="text-align: center; margin-top: 30px; color: #666;">
                    ¿Problemas con la verificación?<br>
                    Puedes solicitar un nuevo código desde la aplicación.
                </p>
            </div>
            
            <div class="footer">
                <p>Este es un email automático, por favor no responder.</p>
                <p style="font-size: 12px; color: #999;">
                    App Accesible © 2025 | Diseñado para ser inclusivo
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Versión de texto plano para lectores de pantalla
    text_content = f"""
    🔐 Código de Verificación
    
    Hola{"" if not user_name else f" {user_name}"},
    
    Tu código de verificación es:
    
    {code}
    
    (Código espaciado para lectura: {spaced_code})
    
    IMPORTANTE:
    - No compartas este código con nadie
    - El código expira en {expires_minutes} minutos
    - Tienes 5 intentos para ingresar el código correcto
    - Si no solicitaste este código, ignora este email
    
    Ingresa este código en la aplicación para verificar tu cuenta.
    
    ¿Problemas? Puedes solicitar un nuevo código desde la app.
    
    ---
    Este es un email automático, por favor no responder.
    App Accesible © 2025
    """
    
    return await EmailService.send_email([email], subject, html_content, text_content)


# ===== app/routes/auth.py (ACTUALIZAR ENDPOINTS) =====
# Agregar estos nuevos endpoints al router de auth

@router.post("/send-verification-code", response_model=dict)
async def send_verification_code(email_data: dict, request: Request):
    """Enviar código de verificación por email"""
    try:
        from app.services.verification_service import verification_service
        from app.services.security_service import security_service
        
        email = email_data.get("email")
        if not email:
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="Email requerido",
                errors=[AccessibleHelpers.create_accessible_error(
                    message="Debe proporcionar un email",
                    field="email"
                )],
                accessibility_info={
                    "announcement": "Error: Email requerido",
                    "focus_element": "email-field",
                    "haptic_pattern": "error"
                }
            )
        
        # Rate limiting
        client_ip = request.client.host
        rate_limit = await security_service.check_rate_limit(
            ip=client_ip,
            endpoint="send_verification_code",
            max_requests=3,  # Solo 3 códigos por hora
            window_minutes=60
        )
        
        if not rate_limit["allowed"]:
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message=f"Demasiados intentos. Espere {int(rate_limit.get('retry_after', 60) / 60)} minutos.",
                accessibility_info={
                    "announcement": "Demasiados intentos. Espere antes de solicitar otro código.",
                    "haptic_pattern": "warning"
                }
            )
        
        # Buscar usuario
        user = await users_collection.find_user_by_email(email)
        if not user:
            # Por seguridad, no revelar si el email existe
            return AccessibleHelpers.create_accessible_response(
                success=True,
                message="Si el email existe, recibirá un código de verificación",
                accessibility_info={
                    "announcement": "Revise su email para el código de verificación",
                    "haptic_pattern": "info"
                }
            )
        
        # Si ya está verificado
        if user.get("is_verified", False):
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="Esta cuenta ya está verificada",
                accessibility_info={
                    "announcement": "Cuenta ya verificada. Puede iniciar sesión.",
                    "haptic_pattern": "info"
                }
            )
        
        # Enviar código
        user_name = user.get("profile", {}).get("first_name", "")
        email_sent = await verification_service.send_verification_code(email, user_name)
        
        if email_sent:
            return AccessibleHelpers.create_accessible_response(
                success=True,
                message="Código de verificación enviado. Revise su email.",
                data={
                    "expires_in_minutes": verification_service.CODE_EXPIRATION_MINUTES,
                    "max_attempts": verification_service.MAX_ATTEMPTS
                },
                accessibility_info={
                    "announcement": f"Código enviado. Tiene {verification_service.CODE_EXPIRATION_MINUTES} minutos para ingresarlo.",
                    "haptic_pattern": "success"
                }
            )
        else:
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="Error enviando el código. Intente nuevamente.",
                accessibility_info={
                    "announcement": "Error enviando código. Intente nuevamente.",
                    "haptic_pattern": "error"
                }
            )
            
    except Exception as e:
        logger.error(f"❌ Error enviando código: {e}")
        return AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error interno del servidor",
            accessibility_info={
                "announcement": "Error del servidor. Intente más tarde.",
                "haptic_pattern": "error"
            }
        )


@router.post("/verify-code", response_model=dict)
async def verify_code(verification_data: dict):
    """Verificar código de verificación"""
    try:
        from app.services.verification_service import verification_service
        
        email = verification_data.get("email")
        code = verification_data.get("code")
        
        if not email or not code:
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="Email y código son requeridos",
                errors=[AccessibleHelpers.create_accessible_error(
                    message="Faltan datos requeridos",
                    field="email" if not email else "code"
                )],
                accessibility_info={
                    "announcement": "Error: Falta información requerida",
                    "focus_element": "email-field" if not email else "code-field",
                    "haptic_pattern": "error"
                }
            )
        
        # Limpiar y validar código
        code = code.strip().replace(" ", "")
        if not code.isdigit() or len(code) != 6:
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="Código inválido. Debe ser de 6 dígitos.",
                errors=[AccessibleHelpers.create_accessible_error(
                    message="Formato de código inválido",
                    field="code",
                    suggestion="Ingrese los 6 dígitos del código"
                )],
                accessibility_info={
                    "announcement": "Código inválido. Ingrese 6 dígitos.",
                    "focus_element": "code-field",
                    "haptic_pattern": "error"
                }
            )
        
        # Verificar código
        result = await verification_service.verify_code(email, code)
        
        if result["success"]:
            return AccessibleHelpers.create_accessible_response(
                success=True,
                message="¡Email verificado exitosamente! Ya puede iniciar sesión.",
                data={"verified": True},
                accessibility_info={
                    "announcement": "Email verificado exitosamente. Redirigiendo al inicio de sesión.",
                    "haptic_pattern": "success"
                }
            )
        else:
            error_messages = {
                "user_not_found": "Usuario no encontrado",
                "no_code": "No hay código activo. Solicite uno nuevo.",
                "expired": "Código expirado. Solicite uno nuevo.",
                "max_attempts": "Demasiados intentos. Solicite un nuevo código.",
                "invalid_code": result.get("message", "Código incorrecto"),
                "server_error": "Error del servidor. Intente nuevamente."
            }
            
            error_type = result.get("error_type", "server_error")
            message = error_messages.get(error_type, result.get("message"))
            
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message=message,
                data={
                    "error_type": error_type,
                    "remaining_attempts": result.get("remaining_attempts")
                },
                errors=[AccessibleHelpers.create_accessible_error(
                    message=message,
                    field="code",
                    suggestion="Verifique el código e intente nuevamente" if error_type == "invalid_code" else "Solicite un nuevo código"
                )],
                accessibility_info={
                    "announcement": message,
                    "focus_element": "code-field" if error_type == "invalid_code" else "resend-button",
                    "haptic_pattern": "error"
                }
            )
            
    except Exception as e:
        logger.error(f"❌ Error verificando código: {e}")
        return AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error interno verificando el código",
            accessibility_info={
                "announcement": "Error del servidor. Intente nuevamente.",
                "haptic_pattern": "error"
            }
        )


@router.post("/skip-verification", response_model=dict)
async def skip_verification(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Permitir al usuario usar la app sin verificar (con limitaciones)"""
    try:
        # Verificar token
        payload = await auth_service.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user_id = payload.get("sub")
        
        # Marcar que el usuario decidió verificar después
        await users_collection.update_user(
            user_id,
            {"security.verification_skipped_at": datetime.utcnow()}
        )
        
        return AccessibleHelpers.create_accessible_response(
            success=True,
            message="Puede usar la aplicación. Le recordaremos verificar su email más tarde.",
            data={"verification_skipped": True},
            accessibility_info={
                "announcement": "Continuando sin verificar. Podrá verificar más tarde desde configuración.",
                "haptic_pattern": "info"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error en skip verification: {e}")
        return AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error procesando la solicitud",
            accessibility_info={
                "announcement": "Error. Intente nuevamente.",
                "haptic_pattern": "error"
            }
        )