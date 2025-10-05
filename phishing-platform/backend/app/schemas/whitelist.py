from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WhitelistCreate(BaseModel):
    cliente_id: int
    url: str
    descripcion: Optional[str] = None

class WhitelistUpdate(BaseModel):
    url: Optional[str] = None
    descripcion: Optional[str] = None

class WhitelistResponse(BaseModel):
    id: int
    cliente_id: int
    cliente_nombre: str
    url: str
    descripcion: Optional[str]
    fecha_agregado: datetime
    
    class Config:
        from_attributes = True