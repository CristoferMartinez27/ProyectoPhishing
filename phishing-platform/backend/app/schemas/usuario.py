from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UsuarioCreate(BaseModel):
    nombre_completo: str
    correo: EmailStr
    nombre_usuario: str
    contrasena: str
    rol_id: int

class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    correo: Optional[EmailStr] = None
    activo: Optional[bool] = None
    rol_id: Optional[int] = None
    contrasena: Optional[str] = None  

class UsuarioResponse(BaseModel):
    id: int
    nombre_completo: str
    correo: str
    nombre_usuario: str
    rol_nombre: str
    activo: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True