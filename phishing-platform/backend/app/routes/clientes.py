from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.models.database import get_db
from app.models.models import Cliente, Bitacora, Usuario
from app.schemas.clientes import ClienteCreate, ClienteUpdate, ClienteResponse
from app.utils.auth import require_admin, get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/clientes", tags=["Clientes"])

@router.get("/", response_model=List[ClienteResponse])
def listar_clientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos los clientes"""
    clientes = db.query(Cliente).all()
    return clientes

@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Crea un nuevo cliente"""
    
    # Verificar si ya existe el dominio
    if db.query(Cliente).filter(Cliente.dominio_legitimo == cliente.dominio_legitimo).first():
        raise HTTPException(status_code=400, detail="El dominio ya está registrado")
    
    nuevo_cliente = Cliente(
        nombre=cliente.nombre,
        dominio_legitimo=cliente.dominio_legitimo,
        contacto_nombre=cliente.contacto_nombre,
        contacto_correo=cliente.contacto_correo,
        contacto_telefono=cliente.contacto_telefono,
        activo=True
    )
    
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="CREAR_CLIENTE",
        detalle=f"Creó cliente: {nuevo_cliente.nombre}"
    )
    db.add(bitacora)
    db.commit()
    
    return nuevo_cliente

@router.put("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(
    cliente_id: int,
    cliente_data: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Actualiza un cliente existente"""
    
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Actualizar campos
    if cliente_data.nombre:
        cliente.nombre = cliente_data.nombre
    if cliente_data.dominio_legitimo:
        cliente.dominio_legitimo = cliente_data.dominio_legitimo
    if cliente_data.contacto_nombre is not None:
        cliente.contacto_nombre = cliente_data.contacto_nombre
    if cliente_data.contacto_correo is not None:
        cliente.contacto_correo = cliente_data.contacto_correo
    if cliente_data.contacto_telefono is not None:
        cliente.contacto_telefono = cliente_data.contacto_telefono
    if cliente_data.activo is not None:
        cliente.activo = cliente_data.activo
    
    db.commit()
    db.refresh(cliente)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="ACTUALIZAR_CLIENTE",
        detalle=f"Actualizó cliente: {cliente.nombre}"
    )
    db.add(bitacora)
    db.commit()
    
    return cliente

@router.delete("/{cliente_id}")
def eliminar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Elimina un cliente"""
    
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    nombre_cliente = cliente.nombre
    db.delete(cliente)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="ELIMINAR_CLIENTE",
        detalle=f"Eliminó cliente: {nombre_cliente}"
    )
    db.add(bitacora)
    db.commit()
    
    return {"mensaje": "Cliente eliminado correctamente"}