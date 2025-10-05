from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class SitioCreate(BaseModel):
    cliente_id: int
    url: str
    notas: Optional[str] = None

class SitioResponse(BaseModel):
    id: int
    cliente_id: int
    cliente_nombre: str
    url: str
    dominio: Optional[str]
    ip: Optional[str]
    estado: str
    es_malicioso: bool
    notas: Optional[str]
    fecha_reporte: datetime
    usuario_reporta_nombre: str
    
    class Config:
        from_attributes = True