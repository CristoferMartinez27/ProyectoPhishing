from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models.database import get_db
from models.models import Usuario, Rol, Bitacora
from schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from utils.auth import get_password_hash, require_admin
from datetime import datetime

#rom ..models.database import get_db
#from ..models.models import Usuario, Rol, Bitacora
#from ..schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
#from ..utils.auth import get_password_hash, require_admin

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])

@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Lista todos los usuarios (solo admin)"""
    usuarios = db.query(Usuario).all()
    
    return [
        {
            "id": u.id,
            "nombre_completo": u.nombre_completo,
            "correo": u.correo,
            "nombre_usuario": u.nombre_usuario,
            "rol_nombre": u.rol.nombre.value,
            "activo": u.activo,
            "fecha_creacion": u.fecha_creacion
        }
        for u in usuarios
    ]

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Crea un nuevo usuario (solo admin)"""
    
    # Verificar si ya existe
    if db.query(Usuario).filter(Usuario.nombre_usuario == usuario.nombre_usuario).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    
    if db.query(Usuario).filter(Usuario.correo == usuario.correo).first():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    # Crear usuario
    nuevo_usuario = Usuario(
        nombre_completo=usuario.nombre_completo,
        correo=usuario.correo,
        nombre_usuario=usuario.nombre_usuario,
        contrasena_hash=get_password_hash(usuario.contrasena),
        rol_id=usuario.rol_id,
        activo=True
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="CREAR_USUARIO",
        detalle=f"Creó usuario: {nuevo_usuario.nombre_usuario}"
    )
    db.add(bitacora)
    db.commit()
    
    return {
        "id": nuevo_usuario.id,
        "nombre_completo": nuevo_usuario.nombre_completo,
        "correo": nuevo_usuario.correo,
        "nombre_usuario": nuevo_usuario.nombre_usuario,
        "rol_nombre": nuevo_usuario.rol.nombre.value,
        "activo": nuevo_usuario.activo,
        "fecha_creacion": nuevo_usuario.fecha_creacion
    }

@router.delete("/{usuario_id}")
def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Elimina un usuario (solo admin)"""
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if usuario.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    
    db.delete(usuario)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="ELIMINAR_USUARIO",
        detalle=f"Eliminó usuario: {usuario.nombre_usuario}"
    )
    db.add(bitacora)
    db.commit()
    
    return {"mensaje": "Usuario eliminado correctamente"}

@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Actualiza un usuario existente (solo admin)"""
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizar campos
    if usuario_data.nombre_completo:
        usuario.nombre_completo = usuario_data.nombre_completo
    if usuario_data.correo:
        # Verificar que el correo no exista en otro usuario
        otro = db.query(Usuario).filter(
            Usuario.correo == usuario_data.correo,
            Usuario.id != usuario_id
        ).first()
        if otro:
            raise HTTPException(status_code=400, detail="El correo ya está en uso")
        usuario.correo = usuario_data.correo
    if usuario_data.rol_id:
        usuario.rol_id = usuario_data.rol_id
    if usuario_data.activo is not None:
        usuario.activo = usuario_data.activo
    
    db.commit()
    db.refresh(usuario)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="ACTUALIZAR_USUARIO",
        detalle=f"Actualizó usuario: {usuario.nombre_usuario}"
    )
    db.add(bitacora)
    db.commit()
    
    return {
        "id": usuario.id,
        "nombre_completo": usuario.nombre_completo,
        "correo": usuario.correo,
        "nombre_usuario": usuario.nombre_usuario,
        "rol_nombre": usuario.rol.nombre.value,
        "activo": usuario.activo,
        "fecha_creacion": usuario.fecha_creacion
    }


@router.get("/roles")
def listar_roles(db: Session = Depends(get_db)):
    """Lista todos los roles disponibles"""
    roles = db.query(Rol).all()
    return [{"id": r.id, "nombre": r.nombre.value, "descripcion": r.descripcion} for r in roles]