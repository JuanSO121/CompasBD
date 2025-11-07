# ===== app/models/accessibility.py =====
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AccessibilityEventType(str, Enum):
    """Tipos de eventos de accesibilidad"""
    PREFERENCE_CHANGED = "preference_changed"
    ERROR_ENCOUNTERED = "error_encountered"
    FEATURE_USED = "feature_used"
    TTS_USED = "tts_used"
    VOICE_COMMAND_USED = "voice_command_used"
    NAVIGATION_ERROR = "navigation_error"

class AccessibilityLog(BaseModel):
    """Log de evento de accesibilidad"""
    user_id: str = Field(..., description="ID del usuario")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: AccessibilityEventType = Field(..., description="Tipo de evento")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detalles del evento")
    user_agent: Optional[str] = Field(None, description="User agent del cliente")
    app_version: Optional[str] = Field(None, description="Versión de la aplicación")

class AccessibilityPreferencesUpdate(BaseModel):
    """Actualización de preferencias de accesibilidad"""
    visual_impairment_level: Optional[str] = Field(None, pattern="^(blind|low_vision|none)$")
    screen_reader_user: Optional[bool] = None
    preferred_tts_speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    preferred_font_size: Optional[str] = Field(None, pattern="^(small|medium|large|x-large)$")
    high_contrast_mode: Optional[bool] = None
    dark_mode_enabled: Optional[bool] = None
    haptic_feedback_enabled: Optional[bool] = None
    audio_descriptions_enabled: Optional[bool] = None
    voice_commands_enabled: Optional[bool] = None
    gesture_navigation_enabled: Optional[bool] = None
    extended_timeout_needed: Optional[bool] = None
    slow_animations: Optional[bool] = None
    custom_notification_sounds: Optional[bool] = None
    audio_confirmation_enabled: Optional[bool] = None
    skip_repetitive_content: Optional[bool] = None
    landmark_navigation_preferred: Optional[bool] = None

class DeviceCapabilities(BaseModel):
    """Capacidades detectadas del dispositivo"""
    has_screen_reader: bool = Field(default=False)
    supports_haptic: bool = Field(default=False)
    supports_voice_input: bool = Field(default=False)
    supports_tts: bool = Field(default=False)
    screen_size: Optional[str] = Field(None, pattern="^(small|medium|large)$")
    connection_type: Optional[str] = Field(None, pattern="^(wifi|cellular|unknown)$")
    platform: Optional[str] = Field(None, pattern="^(android)$")

class VoiceCommand(BaseModel):
    """Comando de voz soportado"""
    command: str = Field(..., description="Comando de voz")
    description: str = Field(..., description="Descripción del comando")
    examples: List[str] = Field(default_factory=list, description="Ejemplos de uso")
    category: str = Field(..., description="Categoría del comando")
    accessibility_level: str = Field(default="all", pattern="^(blind|low_vision|all)$")
