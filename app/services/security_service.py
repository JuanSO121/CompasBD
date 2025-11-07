# ===== app/services/security_service.py =====
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging

logger = logging.getLogger(__name__)

class SecurityService:
    """Servicio de seguridad con rate limiting inclusivo"""
    
    def __init__(self):
        self.request_counts: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.cleanup_interval = 60  # segundos
        self._task = None  # referencia a la tarea asíncrona
    
    async def start_background_tasks(self):
        """Iniciar la tarea de limpieza en segundo plano"""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._cleanup_expired_entries())
            logger.info("🧹 Tarea de limpieza de rate limiting iniciada.")
    
    async def _cleanup_expired_entries(self):
        """Limpiar entradas expiradas del rate limiting"""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_keys = [
                    key for key, data in self.request_counts.items()
                    if current_time > data.get("expires", datetime.min)
                ]

                for key in expired_keys:
                    del self.request_counts[key]

                await asyncio.sleep(self.cleanup_interval)

            except Exception as e:
                logger.error(f"❌ Error en limpieza de rate limiting: {e}")
                await asyncio.sleep(self.cleanup_interval)
    
    def get_rate_limit_key(self, ip: str, endpoint: str, user_id: Optional[str] = None) -> str:
        """Generar clave para rate limiting"""
        if user_id:
            return f"user_{user_id}_{endpoint}"
        return f"ip_{ip}_{endpoint}"
    
    async def check_rate_limit(
        self, 
        ip: str, 
        endpoint: str, 
        max_requests: int, 
        window_minutes: int,
        user_id: Optional[str] = None,
        is_accessibility_user: bool = False
    ) -> Dict[str, Any]:
        """
        Verificar rate limiting inclusivo para usuarios con discapacidades
        """
        try:
            key = self.get_rate_limit_key(ip, endpoint, user_id)
            current_time = datetime.utcnow()
            
            # Aplicar límites más generosos para usuarios de accesibilidad
            if is_accessibility_user:
                max_requests = int(max_requests * 1.5)  # 50% más requests permitidos
                window_minutes = int(window_minutes * 1.2)  # 20% más tiempo
            
            window_start = current_time - timedelta(minutes=window_minutes)
            
            if key not in self.request_counts:
                self.request_counts[key] = {
                    "count": 1,
                    "first_request": current_time,
                    "expires": current_time + timedelta(minutes=window_minutes)
                }
                
                return {
                    "allowed": True,
                    "requests_remaining": max_requests - 1,
                    "reset_time": self.request_counts[key]["expires"],
                    "accessibility_bonus": is_accessibility_user
                }
            
            request_data = self.request_counts[key]
            
            # Si la ventana ha expirado, resetear
            if current_time > request_data["expires"]:
                self.request_counts[key] = {
                    "count": 1,
                    "first_request": current_time,
                    "expires": current_time + timedelta(minutes=window_minutes)
                }
                
                return {
                    "allowed": True,
                    "requests_remaining": max_requests - 1,
                    "reset_time": self.request_counts[key]["expires"],
                    "accessibility_bonus": is_accessibility_user
                }
            
            # Verificar si se excedió el límite
            if request_data["count"] >= max_requests:
                return {
                    "allowed": False,
                    "requests_remaining": 0,
                    "reset_time": request_data["expires"],
                    "retry_after": (request_data["expires"] - current_time).total_seconds(),
                    "accessibility_bonus": is_accessibility_user
                }
            
            # Incrementar contador
            self.request_counts[key]["count"] += 1
            
            return {
                "allowed": True,
                "requests_remaining": max_requests - request_data["count"],
                "reset_time": request_data["expires"],
                "accessibility_bonus": is_accessibility_user
            }
            
        except Exception as e:
            logger.error(f"❌ Error en rate limiting: {e}")
            # En caso de error, permitir la request por seguridad
            return {"allowed": True, "error": str(e)}
    
    def is_accessibility_user(self, user_data: Optional[Dict[str, Any]]) -> bool:
        """Determinar si un usuario requiere consideraciones de accesibilidad"""
        if not user_data:
            return False
        
        accessibility = user_data.get("accessibility", {})
        
        return (
            accessibility.get("screen_reader_user", False) or
            accessibility.get("visual_impairment_level") in ["blind", "low_vision"] or
            accessibility.get("extended_timeout_needed", False) or
            accessibility.get("voice_commands_enabled", False)
        )
    
    def get_rate_limits(self) -> Dict[str, Dict[str, int]]:
        """Obtener configuración de rate limits"""
        return {
            "login": {"max_requests": 10, "window_minutes": 1},
            "register": {"max_requests": 5, "window_minutes": 1}, 
            "password_reset": {"max_requests": 3, "window_minutes": 60},
            "api_general": {"max_requests": 1000, "window_minutes": 60},
            "accessibility_update": {"max_requests": 50, "window_minutes": 1}
        }

security_service = SecurityService()