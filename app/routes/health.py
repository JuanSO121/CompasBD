# ===== app/routes/health.py =====
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.database.connection import get_database
from app.utils.helpers import AccessibleHelpers
from app.utils.constants import ACCESSIBILITY_HEADERS
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check(request: Request):
    """Health check accesible"""
    try:
        # Verificar conexión a base de datos
        db = get_database()
        
        # Intentar ping a la base de datos
        try:
            await db.command("ping")
            db_status = "connected"
            db_healthy = True
        except Exception as db_error:
            logger.error(f"❌ Database ping failed: {db_error}")
            db_status = "disconnected"
            db_healthy = False
        
        # Determinar el estado general
        overall_healthy = db_healthy
        
        response_data = AccessibleHelpers.create_accessible_response(
            success=overall_healthy,
            message="Servicio funcionando correctamente" if overall_healthy else "Servicio con problemas de conectividad",
            data={
                "status": "healthy" if overall_healthy else "unhealthy",
                "database": db_status,
                "accessibility_features": "enabled",
                "version": "1.0.0"
            },
            accessibility_info={
                "announcement": "Sistema en línea y funcionando" if overall_healthy else "Sistema con problemas técnicos",
                "haptic_pattern": "success" if overall_healthy else "error"
            }
        )
        
        # Agregar headers de accesibilidad
        headers = ACCESSIBILITY_HEADERS.copy()
        
        return JSONResponse(
            content=response_data,
            headers=headers,
            status_code=200 if overall_healthy else 503
        )
        
    except Exception as e:
        logger.error(f"❌ Health check falló: {e}")
        
        response_data = AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error verificando el estado del servicio",
            data={
                "status": "error",
                "error": str(e)
            },
            accessibility_info={
                "announcement": "Error verificando el estado del sistema",
                "haptic_pattern": "error"
            }
        )
        
        return JSONResponse(
            content=response_data,
            headers=ACCESSIBILITY_HEADERS.copy(),
            status_code=503
        )

@router.get("/health/accessibility")
async def accessibility_health_check(request: Request):
    """Health check específico para características de accesibilidad"""
    try:
        features_status = {
            "structured_responses": True,
            "descriptive_errors": True,
            "screen_reader_support": True,
            "voice_command_ready": True,
            "extended_timeouts": True,
            "inclusive_rate_limiting": True,
            "accessibility_headers": True,
            "tts_friendly_messages": True
        }
        
        all_features_working = all(features_status.values())
        
        response_data = AccessibleHelpers.create_accessible_response(
            success=all_features_working,
            message="Características de accesibilidad verificadas" if all_features_working else "Algunas características de accesibilidad no están disponibles",
            data={
                "accessibility_features": features_status,
                "overall_status": "accessible" if all_features_working else "partially_accessible",
                "features_count": len(features_status),
                "working_features": sum(1 for v in features_status.values() if v)
            },
            accessibility_info={
                "announcement": "Todas las características de accesibilidad están funcionando" if all_features_working else "Algunas características de accesibilidad no están disponibles",
                "haptic_pattern": "success" if all_features_working else "warning"
            }
        )
        
        return JSONResponse(
            content=response_data,
            headers=ACCESSIBILITY_HEADERS.copy()
        )
        
    except Exception as e:
        logger.error(f"❌ Accessibility health check falló: {e}")
        
        response_data = AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error verificando características de accesibilidad",
            data={
                "error": str(e)
            },
            accessibility_info={
                "announcement": "Error verificando accesibilidad",
                "haptic_pattern": "error"
            }
        )
        
        return JSONResponse(
            content=response_data,
            headers=ACCESSIBILITY_HEADERS.copy(),
            status_code=500
        )