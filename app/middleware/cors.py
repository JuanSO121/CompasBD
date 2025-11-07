# ===== app/middleware/cors.py =====
# El CORS ya está configurado en main.py usando FastAPI's CORSMiddleware
# Este archivo puede usarse para configuraciones CORS más específicas si se necesita

from fastapi.middleware.cors import CORSMiddleware

def configure_cors(app):
    """Configurar CORS con consideraciones de accesibilidad"""
    
    # Headers adicionales que pueden ser útiles para tecnologías asistivas
    accessibility_headers = [
        "X-Content-Accessible",
        "X-Screen-Reader-Friendly",
        "X-High-Contrast-Available",
        "X-Voice-Commands-Supported",
        "X-Extended-Timeout-Supported",
        "X-Process-Time",
        "X-Assistive-Tech-Detected",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining", 
        "X-RateLimit-Reset",
        "X-Accessibility-Bonus"
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # En producción, especificar dominios exactos
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=accessibility_headers  # Exponer headers de accesibilidad al frontend
    )
