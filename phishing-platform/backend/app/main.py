from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, usuarios, clientes, sitios, whitelist, takedown, bitacora

app = FastAPI(
    title="Plataforma Anti-Phishing",
    description="Sistema de detección y takedown de sitios fraudulentos",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(sitios.router)
app.include_router(whitelist.router)
app.include_router(takedown.router)
app.include_router(bitacora.router)

# ⬇️ AGREGAR ESTE ENDPOINT AQUÍ ⬇️
@app.get("/setup-database")
def setup_database():
    """Crea las tablas en la base de datos - USAR SOLO UNA VEZ"""
    try:
        from app.models.database import engine, Base, SessionLocal
        from app.models.models import Rol, Usuario
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        try:
            # Verificar si ya existen roles
            rol_existente = db.query(Rol).first()
            
            if not rol_existente:
                # Crear roles
                roles = [
                    Rol(nombre="administrador", descripcion="Acceso completo al sistema"),
                    Rol(nombre="analista", descripcion="Acceso operativo para gestión de incidentes")
                ]
                db.add_all(roles)
                db.commit()
                
                # Crear usuario admin por defecto
                rol_admin = db.query(Rol).filter(Rol.nombre == "administrador").first()
                admin = Usuario(
                    nombre_completo="Administrador del Sistema",
                    correo="admin@phishing-platform.com",
                    nombre_usuario="admin",
                    contrasena_hash=pwd_context.hash("Admin123!"),
                    rol_id=rol_admin.id,
                    activo=True
                )
                db.add(admin)
                db.commit()
                
                return {
                    "success": True,
                    "mensaje": "✅ Base de datos inicializada correctamente",
                    "tablas_creadas": True,
                    "roles_creados": True,
                    "usuario_admin_creado": True,
                    "credenciales": {
                        "usuario": "admin",
                        "password": "Admin123!"
                    }
                }
            else:
                return {
                    "success": True,
                    "mensaje": "✅ Base de datos ya está inicializada",
                    "tablas_creadas": True,
                    "roles_creados": False,
                    "usuario_admin_creado": False,
                    "nota": "Los roles y usuarios ya existen"
                }
                
        finally:
            db.close()
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/create-admin-user")
def create_admin_user():
    """Crea el usuario administrador - USAR SOLO SI NO EXISTE"""
    try:
        from app.models.database import SessionLocal
        from app.models.models import Rol, Usuario
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        db = SessionLocal()
        try:
            # Verificar si ya existe el usuario admin
            usuario_existente = db.query(Usuario).filter(
                Usuario.nombre_usuario == "admin"
            ).first()
            
            if usuario_existente:
                return {
                    "success": False,
                    "mensaje": "⚠️ El usuario admin ya existe",
                    "usuario": "admin"
                }
            
            # Obtener el rol de administrador
            rol_admin = db.query(Rol).filter(Rol.nombre == "administrador").first()
            
            if not rol_admin:
                return {
                    "success": False,
                    "error": "No existe el rol de administrador. Ejecuta /setup-database primero"
                }
            
            # Contraseña simple
            password = "Admin123!"
            
            # IMPORTANTE: Limitar a 72 bytes antes de hashear
            password_truncated = password[:72]
            
            # Crear usuario admin
            admin = Usuario(
                nombre_completo="Administrador del Sistema",
                correo="admin@phishing-platform.com",
                nombre_usuario="admin",
                contrasena_hash=pwd_context.hash(password_truncated),
                rol_id=rol_admin.id,
                activo=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            
            return {
                "success": True,
                "mensaje": "✅ Usuario administrador creado correctamente",
                "credenciales": {
                    "usuario": "admin",
                    "password": "Admin123!",
                    "correo": "admin@phishing-platform.com"
                },
                "usuario_id": admin.id,
                "rol_id": rol_admin.id
            }
            
        finally:
            db.close()
            
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.get("/")
def root():
    return {
        "mensaje": "API Plataforma Anti-Phishing",
        "version": "1.0.0",
        "estado": "activo"
    }

