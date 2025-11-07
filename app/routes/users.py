# ===== app/routes/users.py =====
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.models.user import User
from app.services.auth_service import auth_service
from app.services.user_service import user_service
from app.database.collections import users_collection
from app.utils.helpers import AccessibleHelpers
from app.utils.validators import AccessibleValidators
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtener usuario actual del token"""
    try:
        payload = await auth_service.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user_id = payload.get("sub")
        user = await users_collection.find_user_by_id(user_id)
        if not user or not user.get("is_active"):
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        return user
    except Exception as e:
        logger.error(f"❌ Error obteniendo usuario actual: {e}")
        raise HTTPException(status_code=401, detail="No autorizado")

@router.get("/profile", response_model=dict)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Obtener perfil del usuario actual"""
    try:
        # Remover información sensible
        user_data = current_user.copy()
        user_data.pop("password_hash", None)
        user_data.pop("security", None)
        user_data["id"] = str(user_data.pop("_id"))

        return AccessibleHelpers.create_accessible_response(
            success=True,
            message="Perfil obtenido exitosamente",
            data={"user": user_data},
            accessibility_info={
                "announcement": "Perfil cargado exitosamente",
                "haptic_pattern": "success"
            }
        )

    except Exception as e:
        logger.error(f"❌ Error obteniendo perfil: {e}")
        return AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error obteniendo el perfil",
            accessibility_info={
                "announcement": "Error cargando perfil",
                "focus_element": "error-message",
                "haptic_pattern": "error"
            }
        )

@router.put("/profile", response_model=dict)
async def update_user_profile(
    profile_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Actualizar perfil del usuario"""
    try:
        # Validar campos si están presentes
        errors = []
        
        if "first_name" in profile_data and profile_data["first_name"]:
            name_validation = AccessibleValidators.validate_name_accessible(
                profile_data["first_name"], "nombre"
            )
            if not name_validation["valid"]:
                errors.append(AccessibleHelpers.create_accessible_error(
                    message=name_validation["message"],
                    field="first_name",
                    suggestion=name_validation.get("suggestions", ["Verifique el nombre"])[0]
                ))
            else:
                profile_data["profile.first_name"] = name_validation["normalized_name"]

        if "last_name" in profile_data and profile_data["last_name"]:
            lastname_validation = AccessibleValidators.validate_name_accessible(
                profile_data["last_name"], "apellido"
            )
            if not lastname_validation["valid"]:
                errors.append(AccessibleHelpers.create_accessible_error(
                    message=lastname_validation["message"],
                    field="last_name",
                    suggestion=lastname_validation.get("suggestions", ["Verifique el apellido"])[0]
                ))
            else:
                profile_data["profile.last_name"] = lastname_validation["normalized_name"]

        if "phone" in profile_data:
            phone_validation = AccessibleValidators.validate_phone_accessible(profile_data["phone"])
            if not phone_validation["valid"]:
                errors.append(AccessibleHelpers.create_accessible_error(
                    message=phone_validation["message"],
                    field="phone",
                    suggestion=phone_validation.get("suggestions", ["Verifique el teléfono"])[0]
                ))
            else:
                profile_data["profile.phone"] = phone_validation.get("normalized_phone")

        if errors:
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="Errores en los datos del perfil",
                errors=errors,
                accessibility_info={
                    "announcement": "Hay errores en los datos. Verifique los campos marcados.",
                    "focus_element": errors[0]["field"],
                    "haptic_pattern": "error"
                }
            )

        # Actualizar perfil
        success = await user_service.update_user_profile(str(current_user["_id"]), profile_data)
        
        if not success:
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="Error actualizando el perfil",
                accessibility_info={
                    "announcement": "Error actualizando perfil. Intente nuevamente.",
                    "focus_element": "error-message",
                    "haptic_pattern": "error"
                }
            )

        return AccessibleHelpers.create_accessible_response(
            success=True,
            message="Perfil actualizado exitosamente",
            accessibility_info={
                "announcement": "Perfil actualizado exitosamente",
                "haptic_pattern": "success"
            }
        )

    except Exception as e:
        logger.error(f"❌ Error actualizando perfil: {e}")
        return AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error interno actualizando perfil",
            accessibility_info={
                "announcement": "Error del servidor. Intente nuevamente.",
                "focus_element": "error-message",
                "haptic_pattern": "error"
            }
        )

@router.delete("/account", response_model=dict)
async def delete_user_account(
    confirmation: dict,
    current_user: dict = Depends(get_current_user)
):
    """Eliminar cuenta de usuario con confirmación accesible"""
    try:
        # Verificar confirmación
        if confirmation.get("confirm_deletion") != "DELETE_MY_ACCOUNT":
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="Confirmación requerida para eliminar la cuenta",
                errors=[AccessibleHelpers.create_accessible_error(
                    message="Debe escribir 'DELETE_MY_ACCOUNT' para confirmar",
                    field="confirm_deletion",
                    suggestion="Escriba exactamente 'DELETE_MY_ACCOUNT' para confirmar la eliminación"
                )],
                accessibility_info={
                    "announcement": "Confirmación requerida. Escriba DELETE_MY_ACCOUNT para confirmar.",
                    "focus_element": "confirm-deletion-field",
                    "haptic_pattern": "warning"
                }
            )

        # Verificar contraseña si se proporciona
        if "password" in confirmation:
            if not auth_service.verify_password(confirmation["password"], current_user["password_hash"]):
                return AccessibleHelpers.create_accessible_response(
                    success=False,
                    message="Contraseña incorrecta",
                    errors=[AccessibleHelpers.create_accessible_error(
                        message="Contraseña incorrecta para confirmar eliminación",
                        field="password",
                        suggestion="Ingrese su contraseña actual"
                    )],
                    accessibility_info={
                        "announcement": "Contraseña incorrecta. Verifique su contraseña.",
                        "focus_element": "password-field",
                        "haptic_pattern": "error"
                    }
                )

        # Eliminar cuenta
        success = await user_service.delete_user_account(str(current_user["_id"]))
        
        if not success:
            return AccessibleHelpers.create_accessible_response(
                success=False,
                message="Error eliminando la cuenta",
                accessibility_info={
                    "announcement": "Error eliminando cuenta. Contacte soporte.",
                    "focus_element": "error-message",
                    "haptic_pattern": "error"
                }
            )

        return AccessibleHelpers.create_accessible_response(
            success=True,
            message="Cuenta eliminada exitosamente. Lamentamos verlo partir.",
            accessibility_info={
                "announcement": "Cuenta eliminada exitosamente. Será redirigido a la página principal.",
                "focus_element": "main-content",
                "haptic_pattern": "success"
            }
        )

    except Exception as e:
        logger.error(f"❌ Error eliminando cuenta: {e}")
        return AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error interno eliminando cuenta",
            accessibility_info={
                "announcement": "Error del servidor. Contacte soporte técnico.",
                "focus_element": "error-message",
                "haptic_pattern": "error"
            }
        )

@router.get("/activity-log", response_model=dict)
async def get_activity_log(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Obtener log de actividad del usuario"""
    try:
        logs = await user_service.get_user_activity_log(str(current_user["_id"]), limit)
        
        return AccessibleHelpers.create_accessible_response(
            success=True,
            message=f"Se encontraron {len(logs)} eventos en su historial de actividad",
            data={"activity_logs": logs, "total_count": len(logs)},
            accessibility_info={
                "announcement": f"Historial cargado. {len(logs)} eventos encontrados.",
                "haptic_pattern": "success"
            }
        )

    except Exception as e:
        logger.error(f"❌ Error obteniendo logs de actividad: {e}")
        return AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error obteniendo historial de actividad",
            accessibility_info={
                "announcement": "Error cargando historial",
                "focus_element": "error-message",
                "haptic_pattern": "error"
            }
        )