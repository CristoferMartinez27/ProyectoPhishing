from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models.database import get_db
from models.models import Sitio, Cliente, Usuario, Bitacora, Whitelist
from schemas.sitio import SitioCreate, SitioResponse
from utils.auth import get_current_user
from datetime import datetime
from urllib.parse import urlparse
from services.validacion_apis import ValidadorAPIs

router = APIRouter(prefix="/api/sitios", tags=["Sitios"])

@router.get("/", response_model=List[SitioResponse])
def listar_sitios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos los sitios reportados"""
    sitios = db.query(Sitio).all()
    
    return [
        {
            "id": s.id,
            "cliente_id": s.cliente_id,
            "cliente_nombre": s.cliente.nombre,
            "url": s.url,
            "dominio": s.dominio,
            "ip": s.ip,
            "estado": s.estado.value,
            "es_malicioso": s.es_malicioso or False,
            "notas": s.notas,
            "fecha_reporte": s.fecha_reporte,
            "usuario_reporta_nombre": s.usuario_reporta.nombre_completo
        }
        for s in sitios
    ]

@router.post("/", response_model=SitioResponse, status_code=status.HTTP_201_CREATED)
def reportar_sitio(
    sitio: SitioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Reporta un nuevo sitio sospechoso"""
    
    # Verificar que el cliente existe
    cliente = db.query(Cliente).filter(Cliente.id == sitio.cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Extraer dominio de la URL
    try:
        parsed = urlparse(sitio.url if sitio.url.startswith('http') else f'http://{sitio.url}')
        dominio = parsed.netloc or parsed.path.split('/')[0]
    except:
        dominio = sitio.url
    
    # Verificar si la URL está en whitelist
    whitelist_entry = db.query(Whitelist).filter(
        Whitelist.cliente_id == sitio.cliente_id,
        Whitelist.url.contains(dominio)
    ).first()
    
    if whitelist_entry:
        raise HTTPException(
            status_code=400, 
            detail="Esta URL está en la whitelist y no puede ser reportada como maliciosa"
        )
    
    # Verificar si ya existe
    sitio_existente = db.query(Sitio).filter(
        Sitio.url == sitio.url,
        Sitio.cliente_id == sitio.cliente_id
    ).first()
    
    if sitio_existente:
        raise HTTPException(status_code=400, detail="Esta URL ya fue reportada anteriormente")
    
    # Crear sitio
    nuevo_sitio = Sitio(
        cliente_id=sitio.cliente_id,
        usuario_reporta_id=current_user.id,
        url=sitio.url,
        dominio=dominio,
        estado="pendiente",
        es_malicioso=False,
        notas=sitio.notas,
        fecha_reporte=datetime.utcnow()
    )
    
    db.add(nuevo_sitio)
    db.commit()
    db.refresh(nuevo_sitio)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="REPORTAR_SITIO",
        detalle=f"Reportó sitio: {nuevo_sitio.url} para cliente {cliente.nombre}"
    )
    db.add(bitacora)
    db.commit()
    
    return {
        "id": nuevo_sitio.id,
        "cliente_id": nuevo_sitio.cliente_id,
        "cliente_nombre": cliente.nombre,
        "url": nuevo_sitio.url,
        "dominio": nuevo_sitio.dominio,
        "ip": nuevo_sitio.ip,
        "estado": nuevo_sitio.estado.value,
        "es_malicioso": nuevo_sitio.es_malicioso,
        "notas": nuevo_sitio.notas,
        "fecha_reporte": nuevo_sitio.fecha_reporte,
        "usuario_reporta_nombre": current_user.nombre_completo
    }

@router.delete("/{sitio_id}")
def eliminar_sitio(
    sitio_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un sitio reportado"""
    
    sitio = db.query(Sitio).filter(Sitio.id == sitio_id).first()
    if not sitio:
        raise HTTPException(status_code=404, detail="Sitio no encontrado")
    
    url_sitio = sitio.url
    db.delete(sitio)
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="ELIMINAR_SITIO",
        detalle=f"Eliminó sitio reportado: {url_sitio}"
    )
    db.add(bitacora)
    db.commit()
    
    return {"mensaje": "Sitio eliminado correctamente"}

@router.post("/{sitio_id}/validar")
def validar_sitio(
    sitio_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Valida un sitio usando APIs externas"""
    
    sitio = db.query(Sitio).filter(Sitio.id == sitio_id).first()
    if not sitio:
        raise HTTPException(status_code=404, detail="Sitio no encontrado")
    
    validador = ValidadorAPIs()
    resultados = []
    
    # Validar con VirusTotal
    vt_result = validador.validar_virustotal(sitio.url)
    resultados.append(vt_result)
    
    # Validar con Google Safe Browsing
    gsb_result = validador.validar_google_safe_browsing(sitio.url)
    resultados.append(gsb_result)
    
    # Contar cuántas APIs detectaron como malicioso
    detecciones_maliciosas = sum(1 for r in resultados if r.get('malicioso', False))
    
    # Actualizar sitio
    sitio.es_malicioso = detecciones_maliciosas > 0
    sitio.estado = "validado" if detecciones_maliciosas > 0 else "falso_positivo"
    sitio.fecha_validacion = datetime.utcnow()
    
    # Guardar validaciones en la tabla
    from models.models import ValidacionApi
    import json
    
    for resultado in resultados:
        validacion = ValidacionApi(
            sitio_id=sitio.id,
            servicio=resultado.get('servicio', 'Desconocido'),
            resultado=json.dumps(resultado),
            es_malicioso=resultado.get('malicioso', False),
            fecha_consulta=datetime.utcnow()
        )
        db.add(validacion)
    
    db.commit()
    
    # Registrar en bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="VALIDAR_SITIO",
        detalle=f"Validó sitio {sitio.url} - Resultado: {'Malicioso' if sitio.es_malicioso else 'Limpio'}"
    )
    db.add(bitacora)
    db.commit()
    
    return {
        "sitio_id": sitio.id,
        "url": sitio.url,
        "es_malicioso": sitio.es_malicioso,
        "estado": sitio.estado.value,
        "validaciones": resultados
    }