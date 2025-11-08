import os
import requests
from typing import List
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    """Servicio para envío de emails via Brevo API (antes Sendinblue)"""
    
    def __init__(self):
        self.brevo_api_key = os.getenv('BREVO_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'cristofermartinezmonroy@gmail.com')
        self.from_name = os.getenv('FROM_NAME', 'PhishGuard Security Team')
        self.api_url = "https://api.brevo.com/v3/smtp/email"
        
    def verificar_configuracion(self) -> bool:
        """Verifica que la API Key de Brevo esté configurada"""
        return bool(self.brevo_api_key)
    
    def test_connection(self) -> dict:
        """Prueba la configuración de Brevo"""
        if not self.verificar_configuracion():
            return {
                "success": False,
                "error": "BREVO_API_KEY no está configurada"
            }
        
        # Hacer una petición de prueba a la API
        headers = {
            "api-key": self.brevo_api_key,
            "Content-Type": "application/json"
        }
        
        try:
            # Endpoint para obtener info de la cuenta
            response = requests.get(
                "https://api.brevo.com/v3/account",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                account_info = response.json()
                return {
                    "success": True,
                    "mensaje": "Configuración de Brevo válida",
                    "from_email": self.from_email,
                    "plan": account_info.get("plan", [{}])[0].get("type", "unknown") if account_info.get("plan") else "unknown"
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "API Key de Brevo inválida"
                }
            else:
                return {
                    "success": False,
                    "error": f"Error al verificar cuenta de Brevo: {response.status_code}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error al conectar con Brevo: {str(e)}"
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
        Envía un email usando la API de Brevo
        
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
                "error": "BREVO_API_KEY no está configurada. Configúrala en las variables de entorno de Railway."
            }
        
        try:
            # Construir payload para Brevo
            payload = {
                "sender": {
                    "name": self.from_name,
                    "email": self.from_email
                },
                "to": [{"email": email} for email in destinatarios],
                "subject": asunto,
                "textContent": cuerpo
            }
            
            # Agregar CC si existe
            if cc:
                payload["cc"] = [{"email": email} for email in cc]
            
            # Agregar BCC si existe
            if bcc:
                payload["bcc"] = [{"email": email} for email in bcc]
            
            # Headers para la API
            headers = {
                "api-key": self.brevo_api_key,
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
            if response.status_code == 201:
                total_destinatarios = len(destinatarios) + (len(cc) if cc else 0) + (len(bcc) if bcc else 0)
                response_data = response.json()
                return {
                    "success": True,
                    "mensaje": f"Email enviado exitosamente a {total_destinatarios} destinatario(s)",
                    "destinatarios": destinatarios + (cc if cc else []) + (bcc if bcc else []),
                    "message_id": response_data.get("messageId")
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "API Key de Brevo inválida. Verifica que sea correcta."
                }
            elif response.status_code == 400:
                error_data = response.json()
                return {
                    "success": False,
                    "error": f"Datos inválidos: {error_data.get('message', 'Error desconocido')}"
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    "success": False,
                    "error": f"Error de Brevo ({response.status_code}): {error_data.get('message', 'Error desconocido')}"
                }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout al conectar con Brevo API"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Error de red al conectar con Brevo: {str(e)}"
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