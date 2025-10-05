from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    nombre_usuario: str
    contrasena: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: dict

class UsuarioResponse(BaseModel):
    id: int
    nombre_completo: str
    correo: str
    nombre_usuario: str
    rol: str
    activo: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True