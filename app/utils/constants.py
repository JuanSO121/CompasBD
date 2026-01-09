# ===== app/utils/constants.py =====

# Formato de respuesta estándar para accesibilidad
ACCESSIBILITY_RESPONSE_FORMAT = {
    "success": bool,
    "message": str,
    "message_type": str,  # "success", "error", "warning", "info"
    "data": dict,
    "accessibility_info": {
        "announcement": str,
        "focus_element": str,
        "haptic_pattern": str  # "success", "error", "warning", "info"
    },
    "errors": list,
    "timestamp": str
}

# Configuraciones por defecto de accesibilidad
DEFAULT_ACCESSIBILITY_PREFERENCES = {
    "visual_impairment_level": "none",
    "screen_reader_user": False,
    "preferred_tts_speed": 1.0,
    "preferred_font_size": "medium",
    "high_contrast_mode": False,
    "dark_mode_enabled": False,
    "haptic_feedback_enabled": True,
    "audio_descriptions_enabled": False,
    "voice_commands_enabled": False,
    "gesture_navigation_enabled": True,
    "extended_timeout_needed": False,
    "slow_animations": False,
    "custom_notification_sounds": False,
    "audio_confirmation_enabled": True,
    "skip_repetitive_content": True,
    "landmark_navigation_preferred": True
}

# Rate limits por endpoint
RATE_LIMITS = {
    "login": {"max_requests": 10, "window_minutes": 1},
    "register": {"max_requests": 5, "window_minutes": 1},
    "password_reset": {"max_requests": 3, "window_minutes": 60},
    "api_general": {"max_requests": 1000, "window_minutes": 60},
    "accessibility_update": {"max_requests": 50, "window_minutes": 1}
}

# Comandos de voz soportados
SUPPORTED_VOICE_COMMANDS = [
    {
        "command": "navegar al inicio",
        "description": "Ir a la página principal",
        "examples": ["ir al inicio", "página principal", "home"],
        "category": "navigation",
        "accessibility_level": "all"
    },
    {
        "command": "leer contenido",
        "description": "Leer el contenido actual de la pantalla",
        "examples": ["leer página", "qué dice aquí", "leer todo"],
        "category": "reading",
        "accessibility_level": "blind"
    },
    {
        "command": "aumentar contraste",
        "description": "Activar modo de alto contraste",
        "examples": ["alto contraste", "más contraste", "contraste"],
        "category": "visual",
        "accessibility_level": "low_vision"
    },
    {
        "command": "activar modo oscuro",
        "description": "Cambiar a modo oscuro",
        "examples": ["modo oscuro", "tema oscuro", "dark mode"],
        "category": "visual",
        "accessibility_level": "all"
    },
    {
        "command": "aumentar tamaño de texto",
        "description": "Aumentar el tamaño de la fuente",
        "examples": ["texto más grande", "agrandar letras"],
        "category": "visual",
        "accessibility_level": "low_vision"
    },
    {
        "command": "activar asistente de voz",
        "description": "Activar comandos de voz",
        "examples": ["activar voz", "comandos de voz"],
        "category": "interaction",
        "accessibility_level": "all"
    }
]

# Headers HTTP específicos de accesibilidad
ACCESSIBILITY_HEADERS = {
    "X-Content-Accessible": "true",
    "X-Screen-Reader-Friendly": "true", 
    "X-High-Contrast-Available": "true",
    "X-Voice-Commands-Supported": "true",
    "X-Extended-Timeout-Supported": "true"
}

# Mensajes de error descriptivos
ERROR_MESSAGES = {
    "EMAIL_ALREADY_EXISTS": "Ya existe una cuenta con este email. ¿Desea iniciar sesión en su lugar?",
    "INVALID_CREDENTIALS": "Email o contraseña incorrectos. Verifique sus datos e intente nuevamente.",
    "ACCOUNT_LOCKED": "Su cuenta está temporalmente bloqueada por seguridad. Intente nuevamente en {minutes} minutos.",
    "EMAIL_NOT_VERIFIED": "Debe verificar su email antes de continuar. ¿Desea que le reenviemos el correo de verificación?",
    "CODE_EXPIRED": "El código de verificación ha expirado. Solicite uno nuevo.",
    "RATE_LIMIT_EXCEEDED": "Ha excedido el límite de intentos. Espere {seconds} segundos antes de intentar nuevamente.",
    "INTERNAL_SERVER_ERROR": "Error interno del servidor. Por favor intente nuevamente en unos momentos.",
    "VALIDATION_ERROR": "Los datos proporcionados no son válidos. Verifique e intente nuevamente.",
    "UNAUTHORIZED": "No está autorizado para realizar esta acción.",
    "NOT_FOUND": "El recurso solicitado no fue encontrado."
}