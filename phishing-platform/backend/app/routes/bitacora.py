from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db
from app.models.models import Bitacora, Usuario
from app.schemas.bitacora import BitacoraResponse
from app.utils.auth import get_current_user, require_admin
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/bitacora", tags=["Bitácora"])

router = APIRouter(prefix="/api/bitacora", tags=["Bitácora"])

@router.get("/", response_model=List[BitacoraResponse])
def listar_bitacora(
    limite: int = Query(100, ge=1, le=1000),
    accion: Optional[str] = None,
    usuario_id: Optional[int] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Lista los registros de bitácora con filtros opcionales (solo admin)"""
    
    query = db.query(Bitacora).order_by(Bitacora.fecha.desc())
    
    # Aplicar filtros
    if accion:
        query = query.filter(Bitacora.accion.contains(accion))
    
    if usuario_id:
        query = query.filter(Bitacora.usuario_id == usuario_id)
    
    if fecha_desde:
        try:
            fecha_inicio = datetime.fromisoformat(fecha_desde)
            query = query.filter(Bitacora.fecha >= fecha_inicio)
        except:
            pass
    
    if fecha_hasta:
        try:
            fecha_fin = datetime.fromisoformat(fecha_hasta)
            query = query.filter(Bitacora.fecha <= fecha_fin)
        except:
            pass
    
    bitacoras = query.limit(limite).all()
    
    return [
        {
            "id": b.id,
            "usuario_id": b.usuario_id,
            "usuario_nombre": b.usuario.nombre_completo,
            "accion": b.accion,
            "detalle": b.detalle,
            "ip_origen": b.ip_origen,
            "fecha": b.fecha
        }
        for b in bitacoras
    ]

@router.get("/acciones")
def listar_tipos_acciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Lista todos los tipos de acciones registradas"""
    
    acciones = db.query(Bitacora.accion).distinct().all()
    return [a[0] for a in acciones]

@router.get("/usuario/{usuario_id}", response_model=List[BitacoraResponse])
def listar_bitacora_usuario(
    usuario_id: int,
    limite: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Lista las acciones de un usuario específico"""
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    bitacoras = db.query(Bitacora).filter(
        Bitacora.usuario_id == usuario_id
    ).order_by(Bitacora.fecha.desc()).limit(limite).all()
    
    return [
        {
            "id": b.id,
            "usuario_id": b.usuario_id,
            "usuario_nombre": b.usuario.nombre_completo,
            "accion": b.accion,
            "detalle": b.detalle,
            "ip_origen": b.ip_origen,
            "fecha": b.fecha
        }
        for b in bitacoras
    ]

@router.get("/estadisticas")
def estadisticas_bitacora(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Obtiene estadísticas de la bitácora"""
    
    from sqlalchemy import func
    
    # Total de registros
    total = db.query(func.count(Bitacora.id)).scalar()
    
    # Registros últimas 24 horas
    hace_24h = datetime.utcnow() - timedelta(hours=24)
    ultimas_24h = db.query(func.count(Bitacora.id)).filter(
        Bitacora.fecha >= hace_24h
    ).scalar()
    
    # Acciones más frecuentes
    acciones_frecuentes = db.query(
        Bitacora.accion,
        func.count(Bitacora.id).label('cantidad')
    ).group_by(Bitacora.accion).order_by(func.count(Bitacora.id).desc()).limit(10).all()
    
    # Usuarios más activos
    usuarios_activos = db.query(
        Usuario.nombre_completo,
        func.count(Bitacora.id).label('acciones')
    ).join(Bitacora).group_by(Usuario.id).order_by(func.count(Bitacora.id).desc()).limit(5).all()
    
    return {
        "total_registros": total,
        "registros_24h": ultimas_24h,
        "acciones_frecuentes": [{"accion": a[0], "cantidad": a[1]} for a in acciones_frecuentes],
        "usuarios_activos": [{"nombre": u[0], "acciones": u[1]} for u in usuarios_activos]
    }