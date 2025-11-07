from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.models.database import get_db
from app.models.models import Takedown, Sitio, Cliente, Bitacora, Usuario
from app.schemas.takedown import TakedownCreate, TakedownUpdate, TakedownResponse
from app.services.takedown_service import TakedownService
from app.utils.auth import get_current_user
from datetime import datetime
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/takedown", tags=["Takedown"])

@router.get("/", response_model=List[TakedownResponse])
def listar_takedowns(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos los takedowns"""
    takedowns = db.query(Takedown).all()
    
    return [
    {
        "id": t.id,
        "sitio_id": t.sitio_id,
        "sitio_url": t.sitio.url,
        "cliente_nombre": t.sitio.cliente.nombre,
        "destinatario": t.destinatario,
        "destinatarios_adicionales": t.destinatarios_adicionales,  # ← AGREGAR
        "asunto": t.asunto,
        "cuerpo": t.cuerpo,
        "estado": t.estado.value,
        "fecha_envio": t.fecha_envio,
        "fecha_confirmacion": t.fecha_confirmacion,
        "respuesta_proveedor": t.respuesta_proveedor
    }
    for t in takedowns
]

@router.get("/sitio/{sitio_id}", response_model=List[TakedownResponse])
def listar_takedowns_por_sitio(
    sitio_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista los takedowns de un sitio específico"""
    sitio = db.query(Sitio).filter(Sitio.id == sitio_id).first()
    if not sitio:
        raise HTTPException(status_code=404, detail="Sitio no encontrado")
    
    takedowns = db.query(Takedown).filter(Takedown.sitio_id == sitio_id).all()
    
    return [
    {
        "id": t.id,
        "sitio_id": t.sitio_id,
        "sitio_url": t.sitio.url,
        "cliente_nombre": t.sitio.cliente.nombre,
        "destinatario": t.destinatario,
        "destinatarios_adicionales": t.destinatarios_adicionales,  # ← AGREGAR
        "asunto": t.asunto,
        "cuerpo": t.cuerpo,
        "estado": t.estado.value,
        "fecha_envio": t.fecha_envio,
        "fecha_confirmacion": t.fecha_confirmacion,
        "respuesta_proveedor": t.respuesta_proveedor
    }
    for t in takedowns
]

@router.post("/generar/{sitio_id}")
def generar_takedown(
    sitio_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Genera una solicitud de takedown para un sitio"""
    
    sitio = db.query(Sitio).filter(Sitio.id == sitio_id).first()
    if not sitio:
        raise HTTPException(status_code=404, detail="Sitio no encontrado")
    
    # Verificar que el sitio esté validado como malicioso
    if not sitio.es_malicioso:
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden generar takedowns para sitios validados como maliciosos"
        )
    
    # Extraer dominio del sitio fraudulento
    from urllib.parse import urlparse
    try:
        parsed = urlparse(sitio.url if sitio.url.startswith('http') else f'http://{sitio.url}')
        dominio_fraudulento = parsed.netloc or parsed.path.split('/')[0]
    except:
        dominio_fraudulento = sitio.dominio or sitio.url
    
    # Generar email de abuse sugerido
    email_abuse = TakedownService.obtener_email_abuse(dominio_fraudulento)
    
    # Generar asunto y cuerpo
    asunto = TakedownService.generar_asunto(
        sitio.url,
        sitio.cliente.nombre
    )
    
    cuerpo = TakedownService.generar_cuerpo_email(
        sitio.url,
        sitio.cliente.nombre,
        sitio.cliente.dominio_legitimo,
        sitio.ip,
        sitio.notas
    )
    
    # Obtener emails comunes
    emails_comunes = TakedownService.obtener_emails_abuse_comunes()
    
    return {
        "sitio_id": sitio.id,
        "sitio_url": sitio.url,
        "destinatario_sugerido": email_abuse,
        "emails_abuse_comunes": emails_comunes,
        "asunto": asunto,
        "cuerpo": cuerpo
    }

@router.post("/", response_model=TakedownResponse, status_code=status.HTTP_201_CREATED)
def crear_takedown(
    takedown: TakedownCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea y registra un takedown con múltiples destinatarios"""
    
    sitio = db.query(Sitio).filter(Sitio.id == takedown.sitio_id).first()
    if not sitio:
        raise HTTPException(status_code=404, detail="Sitio no encontrado")
    
    # Combinar destinatarios
    destinatarios_lista = []
    
    # Agregar destinatario principal
    destinatarios_lista.append(takedown.destinatario_principal)
    
    # Agregar destinatarios secundarios si existen
    if takedown.destinatarios_secundarios:
        destinatarios_lista.extend(takedown.destinatarios_secundarios)
    
    # Eliminar duplicados
    destinatarios_lista = list(set(destinatarios_lista))
    
    # Separar principal del resto
    destinatario_principal = takedown.destinatario_principal
    destinatarios_adicionales = [d for d in destinatarios_lista if d != destinatario_principal]
    
    # Crear takedown
    nuevo_takedown = Takedown(
        sitio_id=takedown.sitio_id,
        destinatario=destinatario_principal,
        destinatarios_adicionales=", ".join(destinatarios_adicionales) if destinatarios_adicionales else None,
        asunto=takedown.asunto,
        cuerpo=takedown.cuerpo,
        estado="pendiente",
        fecha_envio=None
    )
    
    db.add(nuevo_takedown)
    db.commit()
    db.refresh(nuevo_takedown)
    
    # Registrar en bitácora
    total_destinatarios = len(destinatarios_lista)
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="CREAR_TAKEDOWN",
        detalle=f"Creó solicitud de takedown para sitio: {sitio.url} ({total_destinatarios} destinatarios)"
    )
    db.add(bitacora)
    db.commit()
    
    return {
        "id": nuevo_takedown.id,
        "sitio_id": nuevo_takedown.sitio_id,
        "sitio_url": sitio.url,
        "cliente_nombre": sitio.cliente.nombre,
        "destinatario": nuevo_takedown.destinatario,
        "destinatarios_adicionales": nuevo_takedown.destinatarios_adicionales,
        "asunto": nuevo_takedown.asunto,
        "cuerpo": nuevo_takedown.cuerpo,
        "estado": nuevo_takedown.estado.value,
        "fecha_envio": nuevo_takedown.fecha_envio,
        "fecha_confirmacion": nuevo_takedown.fecha_confirmacion,
        "respuesta_proveedor": nuevo_takedown.respuesta_proveedor
    }

@router.post("/{takedown_id}/marcar-enviado")
def marcar_como_enviado(
    takedown_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Marca un takedown como enviado MANUALMENTE (sin enviar email automático)"""
    
    takedown = db.query(Takedown).filter(Takedown.id == takedown_id).first()
    if not takedown:
        raise HTTPException(status_code=404, detail="Takedown no encontrado")
    
    takedown.estado = "enviado"
    takedown.fecha_envio = datetime.utcnow()
    
    # Actualizar estado del sitio
    sitio = takedown.sitio
    sitio.estado = "takedown_enviado"
    
    db.commit()
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="MARCAR_TAKEDOWN_ENVIADO",
        detalle=f"Marcó como enviado manualmente takedown ID: {takedown_id}"
    )
    db.add(bitacora)
    db.commit()
    
    return {"mensaje": "Takedown marcado como enviado"}


@router.post("/{takedown_id}/enviar-email")
def enviar_email_takedown(
    takedown_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Envía el email de takedown automáticamente vía SMTP"""
    
    takedown = db.query(Takedown).filter(Takedown.id == takedown_id).first()
    if not takedown:
        raise HTTPException(status_code=404, detail="Takedown no encontrado")
    
    if takedown.estado != "pendiente":
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden enviar takedowns en estado PENDIENTE"
        )
    
    # Preparar destinatarios
    destinatario_principal = takedown.destinatario
    destinatarios_adicionales = []
    
    if takedown.destinatarios_adicionales:
        destinatarios_adicionales = [
            email.strip() 
            for email in takedown.destinatarios_adicionales.split(',')
        ]
    
    # Enviar email
    email_service = EmailService()
    resultado = email_service.enviar_takedown(
        destinatario_principal=destinatario_principal,
        destinatarios_adicionales=destinatarios_adicionales,
        asunto=takedown.asunto,
        cuerpo=takedown.cuerpo
    )
    
    if not resultado["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"Error al enviar email: {resultado['error']}"
        )
    
    # Actualizar estado
    takedown.estado = "enviado"
    takedown.fecha_envio = datetime.utcnow()
    
    # Actualizar estado del sitio
    sitio = takedown.sitio
    sitio.estado = "takedown_enviado"
    
    db.commit()
    
    # Registrar en bitácora
    total_destinatarios = 1 + len(destinatarios_adicionales)
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="ENVIAR_TAKEDOWN",
        detalle=f"Envió takedown ID {takedown_id} a {total_destinatarios} destinatario(s): {destinatario_principal}"
    )
    db.add(bitacora)
    db.commit()
    
    return {
        "success": True,
        "mensaje": resultado["mensaje"],
        "destinatarios_enviados": resultado["destinatarios"]
    }

@router.put("/{takedown_id}", response_model=TakedownResponse)
def actualizar_takedown(
    takedown_id: int,
    takedown_data: TakedownUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza el estado de un takedown"""
    
    takedown = db.query(Takedown).filter(Takedown.id == takedown_id).first()
    if not takedown:
        raise HTTPException(status_code=404, detail="Takedown no encontrado")
    
    # Actualizar estado
    takedown.estado = takedown_data.estado
    
    if takedown_data.estado == "confirmado":
        takedown.fecha_confirmacion = datetime.utcnow()
        # Actualizar estado del sitio
        takedown.sitio.estado = "sitio_caido"
        takedown.sitio.fecha_caida = datetime.utcnow()
    
    if takedown_data.respuesta_proveedor:
        takedown.respuesta_proveedor = takedown_data.respuesta_proveedor
    
    db.commit()
    db.refresh(takedown)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="ACTUALIZAR_TAKEDOWN",
        detalle=f"Actualizó takedown ID: {takedown_id} - Estado: {takedown_data.estado}"
    )
    db.add(bitacora)
    db.commit()
    
    return {
    "id": takedown.id,
    "sitio_id": takedown.sitio_id,
    "sitio_url": takedown.sitio.url,
    "cliente_nombre": takedown.sitio.cliente.nombre,
    "destinatario": takedown.destinatario,
    "destinatarios_adicionales": takedown.destinatarios_adicionales,  # ← AGREGAR
    "asunto": takedown.asunto,
    "cuerpo": takedown.cuerpo,
    "estado": takedown.estado.value,
    "fecha_envio": takedown.fecha_envio,
    "fecha_confirmacion": takedown.fecha_confirmacion,
    "respuesta_proveedor": takedown.respuesta_proveedor
}

@router.delete("/{takedown_id}")
def eliminar_takedown(
    takedown_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un takedown"""
    
    takedown = db.query(Takedown).filter(Takedown.id == takedown_id).first()
    if not takedown:
        raise HTTPException(status_code=404, detail="Takedown no encontrado")
    
    db.delete(takedown)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="ELIMINAR_TAKEDOWN",
        detalle=f"Eliminó takedown ID: {takedown_id}"
    )
    db.add(bitacora)
    db.commit()
    
    return {"mensaje": "Takedown eliminado correctamente"}