# ===== app/routes/accessibility.py =====
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any

from app.models.accessibility import AccessibilityPreferencesUpdate, DeviceCapabilities, VoiceCommand
from app.services.auth_service import auth_service
from app.services.user_service import user_service
from app.database.collections import users_collection
from app.utils.helpers import AccessibleHelpers
from app.utils.constants import SUPPORTED_VOICE_COMMANDS, DEFAULT_ACCESSIBILITY_PREFERENCES
from app.routes.users import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.get("/preferences/{user_id}", response_model=dict)
async def get_accessibility_preferences(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Obtener preferencias de accesibilidad"""
    try:
        # Verificar que el usuario puede acceder a estas preferencias
        if str(current_user["_id"]) != user_id:
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="No autorizado para acceder a estas preferencias",
                accessibility_info={
                    "announcement": "Acceso denegado a preferencias de otro usuario",
                    "focus_element": "error-message",
                    "haptic_pattern": "error"
                }
            )

        user = await users_collection.find_user_by_id(user_id)
        if not user:
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="Usuario no encontrado",
                accessibility_info={
                    "announcement": "Usuario no encontrado",
                    "focus_element": "error-message",
                    "haptic_pattern": "error"
                }
            )

        accessibility_prefs = user.get("accessibility", DEFAULT_ACCESSIBILITY_PREFERENCES)

        return AccessibleHelpers.create_accessible_response(
            success=True,
            message="Preferencias de accesibilidad obtenidas exitosamente",
            data={"preferences": accessibility_prefs},
            accessibility_info={
                "announcement": "Configuraciones de accesibilidad cargadas",
                "haptic_pattern": "success"
            }
        )

    except Exception as e:
        logger.error(f"❌ Error obteniendo preferencias de accesibilidad: {e}")
        return AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error obteniendo preferencias de accesibilidad",
            accessibility_info={
                "announcement": "Error cargando configuraciones",
                "focus_element": "error-message",
                "haptic_pattern": "error"
            }
        )

@router.put("/preferences/{user_id}", response_model=dict)
async def update_accessibility_preferences(
    user_id: str,
    preferences: AccessibilityPreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Actualizar preferencias de accesibilidad"""
    try:
        # Verificar autorización
        if str(current_user["_id"]) != user_id:
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="No autorizado para modificar estas preferencias",
                accessibility_info={
                    "announcement": "Acceso denegado para modificar preferencias de otro usuario",
                    "focus_element": "error-message",
                    "haptic_pattern": "error"
                }
            )

        # Convertir a diccionario excluyendo valores None
        preferences_dict = {
            k: v for k, v in preferences.dict().items() 
            if v is not None
        }

        if not preferences_dict:
            return AccessibleHelpers.create_accessible_response(
                success=True,
                message="No hay preferencias para actualizar",
                accessibility_info={
                    "announcement": "No se realizaron cambios en las configuraciones",
                    "haptic_pattern": "info"
                }
            )

        # Actualizar preferencias
        success = await user_service.update_accessibility_preferences(
            user_id, preferences_dict
        )

        if not success:
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="Error actualizando preferencias de accesibilidad",
                accessibility_info={
                    "announcement": "Error guardando configuraciones. Intente nuevamente.",
                    "focus_element": "error-message",
                    "haptic_pattern": "error"
                }
            )

        # Crear mensaje descriptivo de los cambios
        changes = []
        if "visual_impairment_level" in preferences_dict:
            level_names = {"none": "sin discapacidad visual", "low_vision": "baja visión", "blind": "ceguera"}
            changes.append(f"nivel de discapacidad visual a {level_names.get(preferences_dict['visual_impairment_level'], 'desconocido')}")
        
        if "screen_reader_user" in preferences_dict:
            changes.append(f"uso de lector de pantalla {'activado' if preferences_dict['screen_reader_user'] else 'desactivado'}")
        
        if "preferred_tts_speed" in preferences_dict:
            changes.append(f"velocidad de voz a {preferences_dict['preferred_tts_speed']}")
        
        if "high_contrast_mode" in preferences_dict:
            changes.append(f"alto contraste {'activado' if preferences_dict['high_contrast_mode'] else 'desactivado'}")

        changes_text = f"Se actualizaron: {', '.join(changes)}" if changes else "Configuraciones actualizadas"

        return AccessibleHelpers.create_accessible_response(
            success=True,
            message="Preferencias de accesibilidad actualizadas exitosamente",
            data={"updated_preferences": list(preferences_dict.keys())},
            accessibility_info={
                "announcement": f"Configuraciones guardadas. {changes_text}",
                "haptic_pattern": "success"
            }
        )

    except Exception as e:
        logger.error(f"❌ Error actualizando preferencias: {e}")
        return AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error interno actualizando preferencias",
            accessibility_info={
                "announcement": "Error del servidor actualizando configuraciones",
                "focus_element": "error-message",
                "haptic_pattern": "error"
            }
        )

@router.post("/detect-capabilities", response_model=dict)
async def detect_device_capabilities(
    capabilities: DeviceCapabilities,
    current_user: dict = Depends(get_current_user)
):
    """Detectar y registrar capacidades del dispositivo"""
    try:
        # Registrar las capacidades detectadas en los logs
        await user_service.log_accessibility_event(
            str(current_user["_id"]),
            "feature_used",
            {
                "event": "device_capabilities_detected",
                "capabilities": capabilities.dict()
            }
        )

        # Sugerir configuraciones basadas en las capacidades
        suggestions = []
        
        if capabilities.has_screen_reader:
            suggestions.append("Se detectó un lector de pantalla. Considere activar el modo 'Usuario de lector de pantalla'")
        
        if capabilities.supports_voice_input:
            suggestions.append("Su dispositivo soporta entrada de voz. Puede activar los comandos de voz")
        
        if capabilities.supports_haptic:
            suggestions.append("Su dispositivo soporta vibración. La retroalimentación háptica está disponible")
        
        if capabilities.screen_size == "small":
            suggestions.append("Pantalla pequeña detectada. Considere aumentar el tamaño de fuente")

        return AccessibleHelpers.create_accessible_response(
            success=True,
            message=f"Capacidades del dispositivo detectadas. {len(suggestions)} sugerencias disponibles.",
            data={
                "detected_capabilities": capabilities.dict(),
                "configuration_suggestions": suggestions
            },
            accessibility_info={
                "announcement": f"Dispositivo analizado. {len(suggestions)} sugerencias de configuración disponibles.",
                "haptic_pattern": "success"
            }
        )

    except Exception as e:
        logger.error(f"❌ Error detectando capacidades: {e}")
        return AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error detectando capacidades del dispositivo",
            accessibility_info={
                "announcement": "Error analizando dispositivo",
                "focus_element": "error-message",
                "haptic_pattern": "error"
            }
        )

@router.get("/voice-commands", response_model=dict)
async def get_voice_commands(
    accessibility_level: Optional[str] = None,
    category: Optional[str] = None
):
    """Obtener lista de comandos de voz soportados"""
    try:
        commands = SUPPORTED_VOICE_COMMANDS.copy()
        
        # Filtrar por nivel de accesibilidad
        if accessibility_level:
            commands = [
                cmd for cmd in commands 
                if cmd["accessibility_level"] == accessibility_level or cmd["accessibility_level"] == "all"
            ]
        
        # Filtrar por categoría
        if category:
            commands = [cmd for cmd in commands if cmd["category"] == category]

        # Agrupar por categoría para mejor organización
        commands_by_category = {}
        for cmd in commands:
            cat = cmd["category"]
            if cat not in commands_by_category:
                commands_by_category[cat] = []
            commands_by_category[cat].append(cmd)

        categories = list(commands_by_category.keys())
        total_commands = len(commands)

        return AccessibleHelpers.create_accessible_response(
            success=True,
            message=f"Se encontraron {total_commands} comandos de voz en {len(categories)} categorías",
            data={
                "voice_commands": commands,
                "commands_by_category": commands_by_category,
                "available_categories": categories,
                "total_commands": total_commands
            },
            accessibility_info={
                "announcement": f"{total_commands} comandos de voz disponibles en {len(categories)} categorías",
                "haptic_pattern": "success"
            }
        )

    except Exception as e:
        logger.error(f"❌ Error obteniendo comandos de voz: {e}")
        return AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error obteniendo comandos de voz",
            accessibility_info={
                "announcement": "Error cargando comandos de voz",
                "focus_element": "error-message",
                "haptic_pattern": "error"
            }
        )

@router.post("/log-usage", response_model=dict)
async def log_accessibility_usage(
    usage_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Registrar uso de características de accesibilidad"""
    try:
        # Validar datos de uso
        required_fields = ["feature_used", "event_type"]
        for field in required_fields:
            if field not in usage_data:
                return AccessibleHelpers.create_accessible_response(
                    success=False,
                    message=f"Campo requerido faltante: {field}",
                    accessibility_info={
                        "announcement": f"Error: falta información de {field}",
                        "focus_element": "error-message",
                        "haptic_pattern": "error"
                    }
                )

        # Registrar el uso
        await user_service.log_accessibility_event(
            str(current_user["_id"]),
            usage_data["event_type"],
            {
                "feature_used": usage_data["feature_used"],
                "details": usage_data.get("details", {}),
                "timestamp": usage_data.get("timestamp"),
                "user_agent": usage_data.get("user_agent"),
                "success": usage_data.get("success", True)
            }
        )

        return AccessibleHelpers.create_accessible_response(
            success=True,
            message="Uso de característica registrado exitosamente",
            accessibility_info={
                "announcement": "Actividad registrada para mejorar la experiencia",
                "haptic_pattern": "success"
            }
        )

    except Exception as e:
        logger.error(f"❌ Error registrando uso: {e}")
        return AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error registrando uso de característica",
            accessibility_info={
                "announcement": "Error registrando actividad",
                "haptic_pattern": "error"
            }
        )