from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BitacoraResponse(BaseModel):
    id: int
    usuario_id: int
    usuario_nombre: str
    accion: str
    detalle: Optional[str]
    ip_origen: Optional[str]
    fecha: datetime
    
    class Config:
        from_attributes = True