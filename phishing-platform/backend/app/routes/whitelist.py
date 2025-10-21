from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models.database import get_db
from models.models import Whitelist, Cliente, Bitacora, Usuario
from schemas.whitelist import WhitelistCreate, WhitelistUpdate, WhitelistResponse
from utils.auth import get_current_user, require_admin
from datetime import datetime

router = APIRouter(prefix="/api/whitelist", tags=["Whitelist"])

@router.get("/", response_model=List[WhitelistResponse])
def listar_whitelist(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todas las URLs en whitelist"""
    whitelist = db.query(Whitelist).all()
    
    return [
        {
            "id": w.id,
            "cliente_id": w.cliente_id,
            "cliente_nombre": w.cliente.nombre,
            "url": w.url,
            "descripcion": w.descripcion,
            "fecha_agregado": w.fecha_agregado
        }
        for w in whitelist
    ]

@router.get("/cliente/{cliente_id}", response_model=List[WhitelistResponse])
def listar_whitelist_por_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista las URLs en whitelist de un cliente específico"""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    whitelist = db.query(Whitelist).filter(Whitelist.cliente_id == cliente_id).all()
    
    return [
        {
            "id": w.id,
            "cliente_id": w.cliente_id,
            "cliente_nombre": w.cliente.nombre,
            "url": w.url,
            "descripcion": w.descripcion,
            "fecha_agregado": w.fecha_agregado
        }
        for w in whitelist
    ]

@router.post("/", response_model=WhitelistResponse, status_code=status.HTTP_201_CREATED)
def agregar_a_whitelist(
    whitelist: WhitelistCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Agrega una URL a la whitelist"""
    
    # Verificar que el cliente existe
    cliente = db.query(Cliente).filter(Cliente.id == whitelist.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Verificar si la URL ya está en whitelist
    existente = db.query(Whitelist).filter(
        Whitelist.cliente_id == whitelist.cliente_id,
        Whitelist.url == whitelist.url
    ).first()
    
    if existente:
        raise HTTPException(status_code=400, detail="Esta URL ya está en la whitelist")
    
    # Crear entrada en whitelist
    nueva_whitelist = Whitelist(
        cliente_id=whitelist.cliente_id,
        url=whitelist.url,
        descripcion=whitelist.descripcion,
        fecha_agregado=datetime.utcnow()
    )
    
    db.add(nueva_whitelist)
    db.commit()
    db.refresh(nueva_whitelist)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="AGREGAR_WHITELIST",
        detalle=f"Agregó URL a whitelist: {nueva_whitelist.url} para cliente {cliente.nombre}"
    )
    db.add(bitacora)
    db.commit()
    
    return {
        "id": nueva_whitelist.id,
        "cliente_id": nueva_whitelist.cliente_id,
        "cliente_nombre": cliente.nombre,
        "url": nueva_whitelist.url,
        "descripcion": nueva_whitelist.descripcion,
        "fecha_agregado": nueva_whitelist.fecha_agregado
    }

@router.put("/{whitelist_id}", response_model=WhitelistResponse)
def actualizar_whitelist(
    whitelist_id: int,
    whitelist_data: WhitelistUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza una entrada de whitelist"""
    
    whitelist = db.query(Whitelist).filter(Whitelist.id == whitelist_id).first()
    if not whitelist:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    
    # Actualizar campos
    if whitelist_data.url:
        whitelist.url = whitelist_data.url
    if whitelist_data.descripcion is not None:
        whitelist.descripcion = whitelist_data.descripcion
    
    db.commit()
    db.refresh(whitelist)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="ACTUALIZAR_WHITELIST",
        detalle=f"Actualizó entrada de whitelist ID: {whitelist_id}"
    )
    db.add(bitacora)
    db.commit()
    
    return {
        "id": whitelist.id,
        "cliente_id": whitelist.cliente_id,
        "cliente_nombre": whitelist.cliente.nombre,
        "url": whitelist.url,
        "descripcion": whitelist.descripcion,
        "fecha_agregado": whitelist.fecha_agregado
    }

@router.delete("/{whitelist_id}")
def eliminar_de_whitelist(
    whitelist_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina una URL de la whitelist"""
    
    whitelist = db.query(Whitelist).filter(Whitelist.id == whitelist_id).first()
    if not whitelist:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
    
    url_eliminada = whitelist.url
    cliente_nombre = whitelist.cliente.nombre
    
    db.delete(whitelist)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="ELIMINAR_WHITELIST",
        detalle=f"Eliminó de whitelist: {url_eliminada} del cliente {cliente_nombre}"
    )
    db.add(bitacora)
    db.commit()
    
    return {"mensaje": "URL eliminada de la whitelist correctamente"}