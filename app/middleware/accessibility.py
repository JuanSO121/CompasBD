# ===== app/middleware/accessibility.py =====
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.constants import ACCESSIBILITY_HEADERS
from app.utils.helpers import AccessibleHelpers
import time
import logging

logger = logging.getLogger(__name__)

class AccessibilityMiddleware(BaseHTTPMiddleware):
    """Middleware para mejorar accesibilidad de la API"""
    
    async def dispatch(self, request: Request, call_next):
        # Registrar tiempo de inicio
        start_time = time.time()
        
        # Detectar si es usuario de tecnología asistiva
        user_agent = request.headers.get("user-agent", "").lower()
        is_assistive_tech = self._detect_assistive_technology(user_agent)
        
        # Agregar información al request
        request.state.is_assistive_tech = is_assistive_tech
        request.state.request_start_time = start_time
        
        try:
            response = await call_next(request)
            
            # Agregar headers de accesibilidad
            for header, value in ACCESSIBILITY_HEADERS.items():
                response.headers[header] = value
            
            # Agregar información de timing para usuarios con necesidades especiales
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            # Para usuarios de tecnología asistiva, agregar headers adicionales
            if is_assistive_tech:
                response.headers["X-Assistive-Tech-Detected"] = "true"
                response.headers["X-Extended-Timeout"] = "true"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error en middleware de accesibilidad: {e}")
            
            # Respuesta de error accesible
            error_response = AccessibleHelpers.create_accessible_response(
                success=False,
                message="Error interno del servidor. El equipo técnico ha sido notificado.",
                accessibility_info={
                    "announcement": "Error del servidor. Por favor intente nuevamente en unos momentos.",
                    "focus_element": "error-message",
                    "haptic_pattern": "error"
                }
            )
            
            return JSONResponse(
                status_code=500,
                content=error_response,
                headers=ACCESSIBILITY_HEADERS
            )
    
    def _detect_assistive_technology(self, user_agent: str) -> bool:
        """Detectar tecnologías asistivas en el user agent"""
        assistive_indicators = [
            'nvda',           # NVDA screen reader
            'jaws',           # JAWS screen reader
            'voiceover',      # VoiceOver (macOS/iOS)
            'talkback',       # TalkBack (Android)
            'orca',           # Orca screen reader (Linux)
            'dragon',         # Dragon speech recognition
            'screenreader',   # Generic screen reader
            'accessibility'   # Generic accessibility tool
        ]
        
        return any(indicator in user_agent for indicator in assistive_indicators)
