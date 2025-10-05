from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.database import get_db
from models.models import Usuario, Bitacora
from schemas.auth import LoginRequest, TokenResponse, UsuarioResponse
from utils.auth import verify_password, create_access_token
from datetime import timedelta, datetime
import os

#from ..models.database import get_db
#from ..models.models import Usuario, Bitacora
#from ..schemas.auth import LoginRequest, TokenResponse, UsuarioResponse
#from ..utils.auth import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Endpoint de login - genera token JWT"""
    
    # Buscar usuario
    usuario = db.query(Usuario).filter(
        Usuario.nombre_usuario == request.nombre_usuario,
        Usuario.activo == True
    ).first()
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    # Verificar contraseña
    if not verify_password(request.contrasena, usuario.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    # Crear token
    access_token = create_access_token(
        data={
            "sub": usuario.nombre_usuario,
            "user_id": usuario.id,
            "rol": usuario.rol.nombre.value
        }
    )
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=usuario.id,
        accion="LOGIN",
        detalle=f"Usuario {usuario.nombre_usuario} inició sesión",
        fecha=datetime.utcnow()
    )
    db.add(bitacora)
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": {
            "id": usuario.id,
            "nombre_completo": usuario.nombre_completo,
            "correo": usuario.correo,
            "nombre_usuario": usuario.nombre_usuario,
            "rol": usuario.rol.nombre.value
        }
    }