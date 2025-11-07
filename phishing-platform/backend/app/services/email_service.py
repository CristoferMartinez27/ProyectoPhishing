import os
import requests
from typing import List
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    """Servicio para envío de emails via SendGrid API"""
    
    def __init__(self):
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'cristofermartinezmonroy@gmail.com')
        self.from_name = os.getenv('FROM_NAME', 'PhishGuard Security Team')
        self.api_url = "https://api.sendgrid.com/v3/mail/send"
        
    def verificar_configuracion(self) -> bool:
        """Verifica que la API Key de SendGrid esté configurada"""
        return bool(self.sendgrid_api_key)
    
    def test_connection(self) -> dict:
        """Prueba la configuración de SendGrid"""
        if not self.verificar_configuracion():
            return {
                "success": False,
                "error": "SENDGRID_API_KEY no está configurada"
            }
        
        # Verificar que la API key tenga el formato correcto
        if not self.sendgrid_api_key.startswith('SG.'):
            return {
                "success": False,
                "error": "La API Key de SendGrid debe empezar con 'SG.'"
            }
        
        return {
            "success": True,
            "mensaje": "Configuración de SendGrid válida",
            "from_email": self.from_email
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
        Envía un email usando la API de SendGrid
        
        Args:
            destinatarios: Lista de emails destinatarios principales
            asunto: Asunto del email
            cuerpo: Cuerpo del email (texto plano)
            cc: Lista de emails en copia (opcional)
            bcc: Lista de emails en copia oculta (opcional)
            
        Returns:
            dict con status y mensaje
        """
        
        if not self.verificar_configuracion():
            return {
                "success": False,
                "error": "SENDGRID_API_KEY no está configurada. Configúrala en las variables de entorno de Railway."
            }
        
        try:
            # Construir lista de destinatarios en formato SendGrid
            to_list = [{"email": email} for email in destinatarios]
            
            # Construir payload
            payload = {
                "personalizations": [{
                    "to": to_list,
                    "subject": asunto
                }],
                "from": {
                    "email": self.from_email,
                    "name": self.from_name
                },
                "content": [{
                    "type": "text/plain",
                    "value": cuerpo
                }]
            }
            
            # Agregar CC si existe
            if cc:
                payload["personalizations"][0]["cc"] = [{"email": email} for email in cc]
            
            # Agregar BCC si existe
            if bcc:
                payload["personalizations"][0]["bcc"] = [{"email": email} for email in bcc]
            
            # Headers para la API
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            
            # Enviar petición
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Verificar respuesta
            if response.status_code == 202:
                total_destinatarios = len(destinatarios) + (len(cc) if cc else 0) + (len(bcc) if bcc else 0)
                return {
                    "success": True,
                    "mensaje": f"Email enviado exitosamente a {total_destinatarios} destinatario(s)",
                    "destinatarios": destinatarios + (cc if cc else []) + (bcc if bcc else [])
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "API Key de SendGrid inválida. Verifica que sea correcta y tenga permisos 'Mail Send'."
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "Acceso denegado. Verifica que tu remitente esté verificado en SendGrid (Sender Authentication)."
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    "success": False,
                    "error": f"Error de SendGrid ({response.status_code}): {error_data.get('errors', [{}])[0].get('message', 'Error desconocido')}"
                }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout al conectar con SendGrid API"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Error de red al conectar con SendGrid: {str(e)}"
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