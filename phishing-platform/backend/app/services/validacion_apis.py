import os
import requests
import socket
import time
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# API Keys
VIRUSTOTAL_API_KEY = os.getenv('VIRUSTOTAL_API_KEY', '')
GOOGLE_SAFE_BROWSING_KEY = os.getenv('GOOGLE_SAFE_BROWSING_KEY', '')
ABUSEIPDB_API_KEY = os.getenv('ABUSEIPDB_API_KEY', '')

class ValidadorAPIs:
    """Servicio para validar URLs con múltiples APIs de ciberseguridad"""
    
    @staticmethod
    def obtener_ip_desde_url(url: str) -> str:
        """Extrae y resuelve la IP desde una URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url if url.startswith('http') else f'http://{url}')
            dominio = parsed.netloc or parsed.path.split('/')[0]
            
            # Resolver dominio a IP
            ip = socket.gethostbyname(dominio)
            return ip
        except Exception as e:
            print(f"Error obteniendo IP: {e}")
            return None
    
    @staticmethod
    def validar_virustotal(url: str) -> Dict[str, Any]:
        """Consulta VirusTotal para verificar si una URL es maliciosa"""
        if not VIRUSTOTAL_API_KEY:
            return {"error": "API Key no configurada", "servicio": "VirusTotal"}
        
        try:
            headers = {"x-apikey": VIRUSTOTAL_API_KEY}
            
            # Paso 1: Enviar URL para análisis
            scan_url = "https://www.virustotal.com/api/v3/urls"
            data = {"url": url}
            scan_response = requests.post(scan_url, headers=headers, data=data, timeout=10)
            
            if scan_response.status_code != 200:
                return {"error": f"Error en escaneo: {scan_response.status_code}", "servicio": "VirusTotal"}
            
            scan_result = scan_response.json()
            analysis_id = scan_result.get('data', {}).get('id', '')
            
            if not analysis_id:
                return {"error": "No se obtuvo ID de análisis", "servicio": "VirusTotal"}
            
            # Paso 2: Esperar y consultar resultados (máximo 3 intentos)
            analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
            
            for intento in range(3):
                time.sleep(5)  # Esperar 5 segundos entre intentos
                
                analysis_response = requests.get(analysis_url, headers=headers, timeout=10)
                
                if analysis_response.status_code == 200:
                    data = analysis_response.json()
                    attributes = data.get('data', {}).get('attributes', {})
                    status = attributes.get('status', '')
                    
                    # Si está completo, devolver resultados
                    if status == 'completed':
                        stats = attributes.get('stats', {})
                        malicious = stats.get('malicious', 0)
                        total = sum(stats.values())
                        
                        return {
                            "servicio": "VirusTotal",
                            "malicioso": malicious > 0,
                            "detecciones": malicious,
                            "total_escaneos": total,
                            "detalles": stats
                        }
            
            # Si después de 3 intentos no está listo
            return {
                "error": "Análisis en progreso. Intente de nuevo en 30 segundos.",
                "servicio": "VirusTotal"
            }
            
        except Exception as e:
            return {"error": str(e), "servicio": "VirusTotal"}
    
    @staticmethod
    def validar_google_safe_browsing(url: str) -> Dict[str, Any]:
        """Consulta Google Safe Browsing"""
        if not GOOGLE_SAFE_BROWSING_KEY:
            return {"error": "API Key no configurada", "servicio": "Google Safe Browsing"}
        
        try:
            api_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GOOGLE_SAFE_BROWSING_KEY}"
            
            payload = {
                "client": {
                    "clientId": "phishguard",
                    "clientVersion": "1.0.0"
                },
                "threatInfo": {
                    "threatTypes": [
                        "MALWARE", 
                        "SOCIAL_ENGINEERING", 
                        "UNWANTED_SOFTWARE", 
                        "POTENTIALLY_HARMFUL_APPLICATION"
                    ],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url}]
                }
            }
            
            response = requests.post(api_url, json=payload, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                matches = result.get('matches', [])
                
                return {
                    "servicio": "Google Safe Browsing",
                    "malicioso": len(matches) > 0,
                    "amenazas_detectadas": len(matches),
                    "tipos_amenaza": [m.get('threatType') for m in matches] if matches else [],
                    "detalles": matches
                }
            
            return {"error": f"Error HTTP {response.status_code}", "servicio": "Google Safe Browsing"}
            
        except Exception as e:
            return {"error": str(e), "servicio": "Google Safe Browsing"}
    
    @staticmethod
    def validar_abuseipdb(url: str) -> Dict[str, Any]:
        """Consulta AbuseIPDB para verificar reputación de IP"""
        if not ABUSEIPDB_API_KEY:
            return {"error": "API Key no configurada", "servicio": "AbuseIPDB"}
        
        # Obtener IP desde URL
        ip = ValidadorAPIs.obtener_ip_desde_url(url)
        
        if not ip:
            return {"error": "No se pudo resolver la IP del dominio", "servicio": "AbuseIPDB"}
        
        try:
            api_url = "https://api.abuseipdb.com/api/v2/check"
            headers = {
                "Key": ABUSEIPDB_API_KEY,
                "Accept": "application/json"
            }
            params = {
                "ipAddress": ip,
                "maxAgeInDays": 90
            }
            
            response = requests.get(api_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                
                score = data.get('abuseConfidenceScore', 0)
                
                return {
                    "servicio": "AbuseIPDB",
                    "ip": ip,
                    "malicioso": score > 25,  # Score mayor a 25 se considera sospechoso
                    "score": score,
                    "reportes": data.get('totalReports', 0),
                    "detalles": data
                }
            
            return {"error": f"Error HTTP {response.status_code}", "servicio": "AbuseIPDB"}
            
        except Exception as e:
            return {"error": str(e), "servicio": "AbuseIPDB"}