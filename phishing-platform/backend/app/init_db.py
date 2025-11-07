from app.models.database import engine, Base, SessionLocal
from app.models.models import Rol, Usuario, Cliente, Whitelist, Sitio, ValidacionApi, Takedown, Bitacora, Estadistica
from sqlalchemy.orm import Session
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_database():
    """Crea todas las tablas y datos iniciales"""
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas exitosamente")
    
    # Crear roles iniciales
    db = SessionLocal()
    try:
        # Verificar si ya existen roles
        rol_existente = db.query(Rol).first()
        if not rol_existente:
            print("\nCreando roles iniciales...")
            roles = [
                Rol(nombre="administrador", descripcion="Acceso completo al sistema"),
                Rol(nombre="analista", descripcion="Acceso operativo para gestión de incidentes")
            ]
            db.add_all(roles)
            db.commit()
            print("✓ Roles creados")
            
            # Crear usuario administrador por defecto
            print("\nCreando usuario administrador...")
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
            print("✓ Usuario administrador creado")
            print("\n" + "="*50)
            print("CREDENCIALES DE ACCESO INICIAL:")
            print("Usuario: admin")
            print("Contraseña: Admin123!")
            print("="*50 + "\n")
        else:
            print("✓ Base de datos ya inicializada")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()