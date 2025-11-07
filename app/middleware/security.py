# ===== app/middleware/security.py =====
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.security_service import security_service
from app.database.collections import users_collection
from app.utils.helpers import AccessibleHelpers
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware de seguridad con consideraciones de accesibilidad"""
    
    # Endpoints que requieren rate limiting específico
    RATE_LIMITED_ENDPOINTS = {
        "/api/v1/auth/login": {"name": "login", "max_requests": 10, "window_minutes": 1},
        "/api/v1/auth/register": {"name": "register", "max_requests": 5, "window_minutes": 1},
        "/api/v1/auth/forgot-password": {"name": "password_reset", "max_requests": 3, "window_minutes": 60},
        "/api/v1/accessibility/preferences": {"name": "accessibility_update", "max_requests": 50, "window_minutes": 1}
    }
    
    async def dispatch(self, request: Request, call_next):
        try:
            # Obtener IP del cliente
            client_ip = self._get_client_ip(request)
            
            # Verificar rate limiting para endpoints específicos
            if request.url.path in self.RATE_LIMITED_ENDPOINTS:
                rate_limit_config = self.RATE_LIMITED_ENDPOINTS[request.url.path]
                
                # Obtener información del usuario si está autenticado
                user_data = await self._get_user_from_request(request)
                is_accessibility_user = security_service.is_accessibility_user(user_data)
                
                rate_limit_result = await security_service.check_rate_limit(
                    ip=client_ip,
                    endpoint=rate_limit_config["name"],
                    max_requests=rate_limit_config["max_requests"],
                    window_minutes=rate_limit_config["window_minutes"],
                    user_id=str(user_data["_id"]) if user_data else None,
                    is_accessibility_user=is_accessibility_user
                )
                
                if not rate_limit_result["allowed"]:
                    retry_after = int(rate_limit_result.get("retry_after", 60))
                    
                    error_response = AccessibleHelpers.create_accessible_response(
                        success=False,
                        message=f"Límite de intentos excedido. Espere {retry_after} segundos antes de intentar nuevamente.",
                        accessibility_info={
                            "announcement": f"Límite excedido. Espere {retry_after} segundos.",
                            "focus_element": "rate-limit-message", 
                            "haptic_pattern": "warning"
                        }
                    )
                    
                    return JSONResponse(
                        status_code=429,
                        content=error_response,
                        headers={
                            "Retry-After": str(retry_after),
                            "X-RateLimit-Limit": str(rate_limit_config["max_requests"]),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(rate_limit_result["reset_time"].timestamp())),
                            "X-Accessibility-Bonus": str(is_accessibility_user).lower()
                        }
                    )
            
            # Continuar con la request
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"❌ Error en middleware de seguridad: {e}")
            
            error_response = AccessibleHelpers.create_accessible_response(
                success=False,
                message="Error de seguridad interno. Intente nuevamente.",
                accessibility_info={
                    "announcement": "Error de seguridad. Intente nuevamente en unos momentos.",
                    "focus_element": "security-error",
                    "haptic_pattern": "error"
                }
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP del cliente considerando proxies"""
        # Verificar headers de proxy
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # IP directa
        return request.client.host if request.client else "unknown"
    
    async def _get_user_from_request(self, request: Request) -> Optional[dict]:
        """Obtener datos del usuario del request si está autenticado"""
        try:
            # Buscar token en headers
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None
            
            token = auth_header.split(" ")[1]
            
            # Verificar token (simplificado para el middleware)
            from app.services.auth_service import auth_service
            payload = await auth_service.verify_token(token)
            
            if payload:
                user_id = payload.get("sub")
                if user_id:
                    return await users_collection.find_user_by_id(user_id)
            
            return None
            
        except Exception:
            return None
