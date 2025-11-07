import os
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    """Servicio para envío de emails via SMTP"""
    
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_name = os.getenv('SMTP_FROM_NAME', 'PhishGuard Security Team')
        
    def verificar_configuracion(self) -> bool:
        """Verifica que las credenciales SMTP estén configuradas"""
        return all([
            self.smtp_host,
            self.smtp_port,
            self.smtp_user,
            self.smtp_password
        ])
    
    def test_connection(self) -> dict:
        """Prueba la conexión SMTP"""
        if not self.verificar_configuracion():
            return {
                "success": False,
                "error": "Configuración SMTP incompleta"
            }
        
        try:
            # Intentar resolver el hostname
            socket.gethostbyname(self.smtp_host)
            
            # Intentar conectar
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as servidor:
                servidor.starttls()
                servidor.login(self.smtp_user, self.smtp_password)
            
            return {
                "success": True,
                "mensaje": "Conexión SMTP exitosa"
            }
        except socket.gaierror:
            return {
                "success": False,
                "error": "No se puede resolver el hostname del servidor SMTP. Verifica la configuración de red."
            }
        except socket.timeout:
            return {
                "success": False,
                "error": "Timeout al conectar con el servidor SMTP. El puerto 587 puede estar bloqueado."
            }
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "error": "Error de autenticación. Verifica usuario y contraseña de aplicación de Gmail."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error de conexión: {str(e)}"
            }
    
    def enviar_email(
        self,
        destinatarios: List[str],
        asunto: str,
        cuerpo: str,
        cc: List[str] = None,
        bcc: List[str] = None
    ) -> dict:
        """
        Envía un email a uno o múltiples destinatarios
        
        Args:
            destinatarios: Lista de emails destinatarios principales
            asunto: Asunto del email
            cuerpo: Cuerpo del email (puede ser texto plano o HTML)
            cc: Lista de emails en copia (opcional)
            bcc: Lista de emails en copia oculta (opcional)
            
        Returns:
            dict con status y mensaje
        """
        
        # Verificar configuración
        if not self.verificar_configuracion():
            return {
                "success": False,
                "error": "Configuración SMTP incompleta. Revise las variables de entorno."
            }
        
        try:
            # Crear mensaje
            mensaje = MIMEMultipart('alternative')
            mensaje['From'] = f"{self.from_name} <{self.smtp_user}>"
            mensaje['To'] = ", ".join(destinatarios)
            mensaje['Subject'] = asunto
            
            # Agregar CC si existe
            if cc:
                mensaje['Cc'] = ", ".join(cc)
            
            # Adjuntar cuerpo
            parte_texto = MIMEText(cuerpo, 'plain', 'utf-8')
            mensaje.attach(parte_texto)
            
            # Preparar lista completa de destinatarios
            todos_destinatarios = destinatarios.copy()
            if cc:
                todos_destinatarios.extend(cc)
            if bcc:
                todos_destinatarios.extend(bcc)
            
            # Conectar y enviar
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as servidor:
                servidor.set_debuglevel(0)  # Cambiar a 1 para debug
                servidor.starttls()
                servidor.login(self.smtp_user, self.smtp_password)
                servidor.sendmail(
                    self.smtp_user,
                    todos_destinatarios,
                    mensaje.as_string()
                )
            
            return {
                "success": True,
                "mensaje": f"Email enviado exitosamente a {len(todos_destinatarios)} destinatario(s)",
                "destinatarios": todos_destinatarios
            }
            
        except socket.gaierror as e:
            return {
                "success": False,
                "error": f"Error de red: No se puede conectar al servidor SMTP. Railway puede estar bloqueando el puerto 587. Error: {str(e)}"
            }
        except socket.timeout:
            return {
                "success": False,
                "error": "Timeout: El servidor SMTP no responde. El puerto 587 puede estar bloqueado por Railway."
            }
        except smtplib.SMTPAuthenticationError:
            return {
                "success": False,
                "error": "Error de autenticación SMTP. Verifica tu usuario y contraseña de aplicación de Gmail."
            }
        except smtplib.SMTPRecipientsRefused as e:
            return {
                "success": False,
                "error": f"Algunos destinatarios fueron rechazados: {str(e)}"
            }
        except smtplib.SMTPException as e:
            return {
                "success": False,
                "error": f"Error SMTP: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error inesperado: {type(e).__name__} - {str(e)}"
            }
    
    def enviar_takedown(
        self,
        destinatario_principal: str,
        destinatarios_adicionales: List[str],
        asunto: str,
        cuerpo: str
    ) -> dict:
        """
        Envía un email de takedown con destinatario principal y CC a proveedores
        
        Args:
            destinatario_principal: Email del hosting específico
            destinatarios_adicionales: Lista de proveedores comunes
            asunto: Asunto del takedown
            cuerpo: Cuerpo del email
            
        Returns:
            dict con status y detalles del envío
        """
        
        return self.enviar_email(
            destinatarios=[destinatario_principal],
            asunto=asunto,
            cuerpo=cuerpo,
            cc=destinatarios_adicionales if destinatarios_adicionales else None
        )