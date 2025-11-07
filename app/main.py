# ===== app/main.py =====
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config.settings import settings
from app.database.connection import connect_to_mongo, close_mongo_connection
from app.middleware.error_handler import register_error_handlers
from app.routes import auth, users, accessibility, health
from app.utils.constants import ACCESSIBILITY_HEADERS
from app.services.security_service import security_service

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    logger.info("🚀 Iniciando aplicación...")
    try:
        await connect_to_mongo()
        await security_service.start_background_tasks()
        logger.info("✅ Aplicación iniciada exitosamente")
    except Exception as e:
        logger.error(f"❌ Error iniciando aplicación: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Cerrando aplicación...")
    await close_mongo_connection()
    logger.info("✅ Aplicación cerrada exitosamente")

# Crear aplicación
app = FastAPI(
    title="API Accesible para Personas con Discapacidad Visual",
    description="Backend con características de accesibilidad integradas",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=list(ACCESSIBILITY_HEADERS.keys())
)

# Middleware para agregar headers de accesibilidad
@app.middleware("http")
async def add_accessibility_headers(request: Request, call_next):
    """Agregar headers de accesibilidad a todas las respuestas"""
    try:
        response = await call_next(request)
        
        # Agregar headers de accesibilidad
        for key, value in ACCESSIBILITY_HEADERS.items():
            response.headers[key] = value
        
        return response
    except Exception as e:
        logger.error(f"❌ Error en middleware: {e}")
        # Si hay error, retornar respuesta de error
        from app.utils.helpers import AccessibleHelpers
        error_response = AccessibleHelpers.create_accessible_response(
            success=False,
            message="Error interno del servidor",
            accessibility_info={
                "announcement": "Error del servidor",
                "haptic_pattern": "error"
            }
        )
        return JSONResponse(
            content=error_response,
            status_code=500,
            headers=ACCESSIBILITY_HEADERS
        )

# Registrar handlers de errores
register_error_handlers(app)

# Registrar routers
app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["Health"]
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Users"]
)

app.include_router(
    accessibility.router,
    prefix="/api/v1/accessibility",
    tags=["Accessibility"]
)

# Endpoint raíz
@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    from app.utils.helpers import AccessibleHelpers
    
    return AccessibleHelpers.create_accessible_response(
        success=True,
        message="API Accesible - Backend para Personas con Discapacidad Visual",
        data={
            "version": "1.0.0",
            "documentation": "/docs",
            "health_check": "/api/v1/health",
            "accessibility_features": {
                "structured_responses": True,
                "screen_reader_friendly": True,
                "descriptive_errors": True,
                "voice_command_support": True,
                "extended_timeouts": True
            }
        },
        accessibility_info={
            "announcement": "API de accesibilidad funcionando",
            "haptic_pattern": "info"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )