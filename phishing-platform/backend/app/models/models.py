from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum

# Enums para tipos específicos
class RolTipo(str, enum.Enum):
    ADMINISTRADOR = "administrador"
    ANALISTA = "analista"

class EstadoSitio(str, enum.Enum):
    PENDIENTE = "pendiente"
    VALIDADO = "validado"
    FALSO_POSITIVO = "falso_positivo"
    TAKEDOWN_ENVIADO = "takedown_enviado"
    SITIO_CAIDO = "sitio_caido"

class EstadoTakedown(str, enum.Enum):
    PENDIENTE = "pendiente"
    ENVIADO = "enviado"
    CONFIRMADO = "confirmado"
    RECHAZADO = "rechazado"

# Tablas
class Rol(Base):
    __tablename__ = "rol"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(Enum(RolTipo), unique=True, nullable=False)
    descripcion = Column(String(255))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    usuarios = relationship("Usuario", back_populates="rol")

class Usuario(Base):
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(255), nullable=False)
    correo = Column(String(255), unique=True, nullable=False, index=True)
    nombre_usuario = Column(String(100), unique=True, nullable=False, index=True)
    contrasena_hash = Column(String(255), nullable=False)
    activo = Column(Boolean, default=True)
    rol_id = Column(Integer, ForeignKey("rol.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    rol = relationship("Rol", back_populates="usuarios")
    bitacoras = relationship("Bitacora", back_populates="usuario")
    sitios_reportados = relationship("Sitio", back_populates="usuario_reporta")

class Cliente(Base):
    __tablename__ = "cliente"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    dominio_legitimo = Column(String(255), nullable=False)
    contacto_nombre = Column(String(255))
    contacto_correo = Column(String(255))
    contacto_telefono = Column(String(50))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    sitios = relationship("Sitio", back_populates="cliente")
    whitelist = relationship("Whitelist", back_populates="cliente")

class Whitelist(Base):
    __tablename__ = "whitelist"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("cliente.id"), nullable=False)
    url = Column(String(500), nullable=False)
    descripcion = Column(Text)
    fecha_agregado = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    cliente = relationship("Cliente", back_populates="whitelist")

class Sitio(Base):
    __tablename__ = "sitio"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("cliente.id"), nullable=False)
    usuario_reporta_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    url = Column(String(500), nullable=False, index=True)
    dominio = Column(String(255), index=True)
    ip = Column(String(50))
    estado = Column(Enum(EstadoSitio), default=EstadoSitio.PENDIENTE)
    es_malicioso = Column(Boolean, default=False)
    notas = Column(Text)
    fecha_reporte = Column(DateTime, default=datetime.utcnow)
    fecha_validacion = Column(DateTime)
    fecha_caida = Column(DateTime)
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="sitios")
    usuario_reporta = relationship("Usuario", back_populates="sitios_reportados")
    validaciones = relationship("ValidacionApi", back_populates="sitio")
    takedowns = relationship("Takedown", back_populates="sitio")

class ValidacionApi(Base):
    __tablename__ = "validacion_api"
    
    id = Column(Integer, primary_key=True, index=True)
    sitio_id = Column(Integer, ForeignKey("sitio.id"), nullable=False)
    servicio = Column(String(100), nullable=False)  # VirusTotal, GSB, AbuseIPDB
    resultado = Column(Text)  # JSON con respuesta completa
    es_malicioso = Column(Boolean)
    fecha_consulta = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    sitio = relationship("Sitio", back_populates="validaciones")

class Takedown(Base):
    __tablename__ = "takedown"
    
    id = Column(Integer, primary_key=True, index=True)
    sitio_id = Column(Integer, ForeignKey("sitio.id"), nullable=False)
    destinatario = Column(String(255), nullable=False)  # Destinatario principal
    destinatarios_adicionales = Column(Text)  # Lista de emails separados por comas
    asunto = Column(String(500))
    cuerpo = Column(Text)
    estado = Column(Enum(EstadoTakedown), default=EstadoTakedown.PENDIENTE)
    fecha_envio = Column(DateTime)
    fecha_confirmacion = Column(DateTime)
    respuesta_proveedor = Column(Text)
    
    # Relación
    sitio = relationship("Sitio", back_populates="takedowns")

class Bitacora(Base):
    __tablename__ = "bitacora"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    accion = Column(String(255), nullable=False)
    detalle = Column(Text)
    ip_origen = Column(String(50))
    fecha = Column(DateTime, default=datetime.utcnow)
    
    # Relación
    usuario = relationship("Usuario", back_populates="bitacoras")

class Estadistica(Base):
    __tablename__ = "estadistica"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("cliente.id"))
    fecha = Column(DateTime, default=datetime.utcnow)
    total_reportes = Column(Integer, default=0)
    sitios_validados = Column(Integer, default=0)
    sitios_caidos = Column(Integer, default=0)
    falsos_positivos = Column(Integer, default=0)