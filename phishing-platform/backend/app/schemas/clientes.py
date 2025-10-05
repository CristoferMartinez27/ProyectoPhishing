from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class ClienteCreate(BaseModel):
    nombre: str
    dominio_legitimo: str
    contacto_nombre: Optional[str] = None
    contacto_correo: Optional[EmailStr] = None
    contacto_telefono: Optional[str] = None

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    dominio_legitimo: Optional[str] = None
    contacto_nombre: Optional[str] = None
    contacto_correo: Optional[EmailStr] = None
    contacto_telefono: Optional[str] = None
    activo: Optional[bool] = None

class ClienteResponse(BaseModel):
    id: int
    nombre: str
    dominio_legitimo: str
    contacto_nombre: Optional[str]
    contacto_correo: Optional[str]
    contacto_telefono: Optional[str]
    activo: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True