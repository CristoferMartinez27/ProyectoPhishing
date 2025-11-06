from models.database import engine, Base, SessionLocal
from models.models import Rol
from sqlalchemy.orm import Session

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
        else:
            print("✓ Roles ya existentes, no se requiere acción")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
