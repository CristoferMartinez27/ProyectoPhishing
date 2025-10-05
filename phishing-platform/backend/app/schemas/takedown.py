from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class TakedownCreate(BaseModel):
    sitio_id: int
    destinatario_principal: EmailStr
    destinatarios_secundarios: Optional[List[EmailStr]] = None
    asunto: Optional[str] = None
    cuerpo: Optional[str] = None

class TakedownUpdate(BaseModel):
    estado: str
    respuesta_proveedor: Optional[str] = None

class TakedownResponse(BaseModel):
    id: int
    sitio_id: int
    sitio_url: str
    cliente_nombre: str
    destinatario: str
    destinatarios_adicionales: Optional[str]
    asunto: str
    cuerpo: str
    estado: str
    fecha_envio: Optional[datetime]
    fecha_confirmacion: Optional[datetime]
    respuesta_proveedor: Optional[str]
    
    class Config:
        from_attributes = True