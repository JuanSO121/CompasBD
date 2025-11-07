# ===== app/models/auth.py =====
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
import re

class UserRegistration(BaseModel):
    """Datos para registro de usuario"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=8, max_length=100, description="Contraseña")
    confirm_password: str = Field(..., description="Confirmación de contraseña")
    
    # Perfil básico opcional
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    preferred_language: str = Field(default="es", pattern="^(es|en)$")
    
    # Configuración inicial de accesibilidad
    visual_impairment_level: str = Field(default="none", pattern="^(blind|low_vision|none)$")
    screen_reader_user: bool = Field(default=False)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Las contraseñas no coinciden')
        return v
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validación de fortaleza de contraseña con mensajes descriptivos"""
        errors = []
        
        if len(v) < 8:
            errors.append("debe tener al menos 8 caracteres")
        
        if not re.search(r'[A-Z]', v):
            errors.append("debe incluir al menos una letra mayúscula")
        
        if not re.search(r'[a-z]', v):
            errors.append("debe incluir al menos una letra minúscula")
        
        if not re.search(r'\d', v):
            errors.append("debe incluir al menos un número")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            errors.append("debe incluir al menos un símbolo especial")
        
        if errors:
            error_msg = f"La contraseña {', '.join(errors)}"
            raise ValueError(error_msg)
        
        return v

class UserLogin(BaseModel):
    """Datos para inicio de sesión"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=1, description="Contraseña")
    remember_me: bool = Field(default=False, description="Recordar sesión")

class PasswordReset(BaseModel):
    """Datos para reseteo de contraseña"""
    email: EmailStr = Field(..., description="Email del usuario")

class PasswordResetConfirm(BaseModel):
    """Confirmación de reseteo de contraseña"""
    token: str = Field(..., min_length=1, description="Token de reseteo")
    new_password: str = Field(..., min_length=8, max_length=100, description="Nueva contraseña")
    confirm_password: str = Field(..., description="Confirmación de contraseña")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v

class TokenPair(BaseModel):
    """Par de tokens JWT"""
    access_token: str = Field(..., description="Token de acceso")
    refresh_token: str = Field(..., description="Token de renovación")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Tiempo de expiración en segundos")

class TokenRefresh(BaseModel):
    """Renovación de token"""
    refresh_token: str = Field(..., min_length=1, description="Token de renovación")
