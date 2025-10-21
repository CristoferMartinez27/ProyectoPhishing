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
    """Elimina un sitio reportado y todos sus registros relacionados"""
    
    sitio = db.query(Sitio).filter(Sitio.id == sitio_id).first()
    if not sitio:
        raise HTTPException(status_code=404, detail="Sitio no encontrado")
    
    url_sitio = sitio.url
    
    # Eliminar primero los registros relacionados
    from models.models import ValidacionApi, Takedown
    
    # Eliminar validaciones
    db.query(ValidacionApi).filter(ValidacionApi.sitio_id == sitio_id).delete()
    
    # Eliminar takedowns
    db.query(Takedown).filter(Takedown.sitio_id == sitio_id).delete()
    
    # Ahora eliminar el sitio
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
    print("Validando con VirusTotal...")
    vt_result = validador.validar_virustotal(sitio.url)
    resultados.append(vt_result)
    
    # Validar con Google Safe Browsing
    print("Validando con Google Safe Browsing...")
    gsb_result = validador.validar_google_safe_browsing(sitio.url)
    resultados.append(gsb_result)
    
    # Validar con AbuseIPDB
    print("Validando con AbuseIPDB...")
    abuse_result = validador.validar_abuseipdb(sitio.url)
    resultados.append(abuse_result)
    
    # Guardar IP si se obtuvo de AbuseIPDB
    if not abuse_result.get('error') and abuse_result.get('ip'):
        sitio.ip = abuse_result.get('ip')
    
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
        detalle=f"Validó sitio {sitio.url} - Resultado: {'Malicioso' if sitio.es_malicioso else 'Limpio'} ({detecciones_maliciosas}/3 APIs)"
    )
    db.add(bitacora)
    db.commit()
    
    return {
        "sitio_id": sitio.id,
        "url": sitio.url,
        "ip": sitio.ip,
        "es_malicioso": sitio.es_malicioso,
        "estado": sitio.estado.value,
        "detecciones": f"{detecciones_maliciosas}/3",
        "validaciones": resultados
    }

@router.get("/estadisticas")
def obtener_estadisticas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene estadísticas para gráficos del dashboard"""
    from sqlalchemy import func
    from datetime import timedelta
    
    # Sitios por estado
    estados = db.query(
        Sitio.estado,
        func.count(Sitio.id).label('cantidad')
    ).group_by(Sitio.estado).all()
    
    sitios_por_estado = {e[0].value: e[1] for e in estados}
    
    # Sitios por cliente (top 5)
    top_clientes = db.query(
        Cliente.nombre,
        func.count(Sitio.id).label('cantidad')
    ).join(Sitio).group_by(Cliente.id).order_by(func.count(Sitio.id).desc()).limit(5).all()
    
    # Actividad últimos 7 días
    hace_7_dias = datetime.utcnow() - timedelta(days=7)
    actividad_semanal = db.query(
        func.date(Sitio.fecha_reporte).label('fecha'),
        func.count(Sitio.id).label('cantidad')
    ).filter(Sitio.fecha_reporte >= hace_7_dias).group_by(func.date(Sitio.fecha_reporte)).all()
    
    # Takedowns por estado
    from models.models import Takedown
    takedowns_estados = db.query(
        Takedown.estado,
        func.count(Takedown.id).label('cantidad')
    ).group_by(Takedown.estado).all()
    
    return {
        "sitios_por_estado": sitios_por_estado,
        "top_clientes": [{"nombre": c[0], "cantidad": c[1]} for c in top_clientes],
        "actividad_semanal": [{"fecha": str(a[0]), "cantidad": a[1]} for a in actividad_semanal],
        "takedowns_estados": {t[0].value: t[1] for t in takedowns_estados}
    }

@router.get("/exportar-csv/{cliente_id}")
def exportar_sitios_csv(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Exporta los sitios reportados de un cliente a CSV"""
    from fastapi.responses import StreamingResponse
    import io
    import csv

    # Verificar que el cliente existe
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Obtener sitios del cliente
    sitios = (
        db.query(Sitio)
        .filter(Sitio.cliente_id == cliente_id)
        .order_by(Sitio.fecha_reporte.desc())
        .all()
    )

    if not sitios:
        raise HTTPException(status_code=404, detail="No hay sitios reportados para este cliente")

    # Crear CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)

    # Encabezados
    writer.writerow([
        "ID","Cliente","URL","Dominio","IP","Estado","Es Malicioso",
        "Reportado Por","Fecha Reporte","Fecha Validación","Fecha Caída","Notas"
    ])

    # Filas
    for sitio in sitios:
        writer.writerow([
            sitio.id,
            cliente.nombre,
            sitio.url,
            sitio.dominio or "",
            sitio.ip or "",
            sitio.estado.value,
            "Sí" if sitio.es_malicioso else "No",
            getattr(sitio.usuario_reporta, "nombre_completo", "") or "",
            sitio.fecha_reporte.strftime("%Y-%m-%d %H:%M:%S") if sitio.fecha_reporte else "",
            sitio.fecha_validacion.strftime("%Y-%m-%d %H:%M:%S") if sitio.fecha_validacion else "",
            sitio.fecha_caida.strftime("%Y-%m-%d %H:%M:%S") if sitio.fecha_caida else "",
            sitio.notas or "",
        ])

    # Bitácora
    bitacora = Bitacora(
        usuario_id=current_user.id,
        accion="EXPORTAR_CSV",
        detalle=f"Exportó reporte CSV del cliente: {cliente.nombre} ({len(sitios)} sitios)",
    )
    db.add(bitacora)
    db.commit()

    # Preparar respuesta
    output.seek(0)
    fecha_actual = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"reporte_{cliente.nombre.replace(' ', '_')}_{fecha_actual}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),  # UTF-8 con BOM para Excel
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"},
    )