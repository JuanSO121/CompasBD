# ===== app/database/connection.py =====
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def connect_to_mongo():
    """Conectar a MongoDB"""
    try:
        db.client = AsyncIOMotorClient(settings.DATABASE_URL)
        db.database = db.client[settings.DATABASE_NAME]
        
        # Verificar conexión
        await db.client.admin.command('ping')
        logger.info("✅ Conectado a MongoDB exitosamente")
        
        # Crear índices
        await create_indexes()
        
    except Exception as e:
        logger.error(f"❌ Error conectando a MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    if db.client:
        db.client.close()
        logger.info("🔄 Conexión a MongoDB cerrada")

async def create_indexes():
    """Crear índices necesarios"""
    try:
        # Índices para usuarios
        users_collection = db.database.users
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("security.email_verification_token")
        await users_collection.create_index("security.password_reset_tokens.token")
        await users_collection.create_index("created_at")
        
        # Índices para logs de accesibilidad
        logs_collection = db.database.accessibility_logs
        await logs_collection.create_index("user_id")
        await logs_collection.create_index("timestamp")
        await logs_collection.create_index("event_type")
        await logs_collection.create_index([("user_id", 1), ("timestamp", -1)])
        
        logger.info("✅ Índices creados exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error creando índices: {e}")

def get_database():
    """Obtener instancia de base de datos"""
    return db.database
