# ===== app/middleware/error_handler.py =====
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.helpers import AccessibleHelpers
from app.utils.constants import ERROR_MESSAGES, ACCESSIBILITY_HEADERS
import logging
import traceback

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler para errores de validación de Pydantic"""
    logger.warning(f"⚠️ Validation error en {request.url.path}: {exc.errors()}")
    
    # Convertir errores de Pydantic a formato accesible
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:]) if len(error["loc"]) > 1 else "general"
        message = error["msg"]
        
        # Mejorar mensajes de error comunes
        if "value_error" in error["type"]:
            if "password" in field.lower():
                message = "La contraseña no cumple con los requisitos de seguridad"
            elif "email" in field.lower():
                message = "El formato del email no es válido"
        
        errors.append(
            AccessibleHelpers.create_accessible_error(
                message=message,
                field=field,
                suggestion="Verifique el formato del campo y vuelva a intentar"
            )
        )
    
    # Determinar el primer campo con error para el foco
    focus_field = errors[0]["field"] if errors else None
    
    response_data = AccessibleHelpers.create_accessible_response(
        success=False,
        message="Los datos proporcionados no son válidos",
        errors=errors,
        accessibility_info={
            "announcement": f"Hay {len(errors)} error{'es' if len(errors) > 1 else ''} en el formulario. Primer error: {errors[0]['message'] if errors else 'datos inválidos'}",
            "focus_element": f"{focus_field}-field" if focus_field else "form",
            "haptic_pattern": "error"
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data,
        headers=ACCESSIBILITY_HEADERS
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handler para excepciones HTTP estándar"""
    logger.warning(f"⚠️ HTTP {exc.status_code} en {request.url.path}: {exc.detail}")
    
    # Mapear códigos HTTP a mensajes accesibles
    status_messages = {
        400: "Solicitud inválida",
        401: "No autorizado. Inicie sesión para continuar",
        403: "No tiene permisos para realizar esta acción",
        404: "El recurso solicitado no fue encontrado",
        405: "Método no permitido",
        429: "Demasiadas solicitudes. Espere un momento e intente nuevamente",
        500: "Error interno del servidor",
        502: "Servicio no disponible temporalmente",
        503: "Servicio en mantenimiento"
    }
    
    message = status_messages.get(exc.status_code, str(exc.detail))
    
    response_data = AccessibleHelpers.create_accessible_response(
        success=False,
        message=message,
        data={"status_code": exc.status_code},
        accessibility_info={
            "announcement": message,
            "haptic_pattern": "error" if exc.status_code >= 500 else "warning"
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=ACCESSIBILITY_HEADERS
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handler para excepciones generales no manejadas"""
    logger.error(f"❌ Error no manejado en {request.url.path}:")
    logger.error(traceback.format_exc())
    
    # En producción, no revelar detalles del error
    error_detail = str(exc) if logger.level == logging.DEBUG else "Error interno del servidor"
    
    response_data = AccessibleHelpers.create_accessible_response(
        success=False,
        message="Ha ocurrido un error inesperado. Por favor intente nuevamente.",
        data={
            "error_type": type(exc).__name__,
            "error_detail": error_detail if logger.level == logging.DEBUG else None
        },
        accessibility_info={
            "announcement": "Error del servidor. Intente nuevamente en unos momentos.",
            "haptic_pattern": "error"
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data,
        headers=ACCESSIBILITY_HEADERS
    )

def register_error_handlers(app):
    """Registrar todos los handlers de errores en la app"""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("✅ Error handlers registrados exitosamente")