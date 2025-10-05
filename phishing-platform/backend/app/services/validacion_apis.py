import os
import requests
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# API Keys (las configuraremos después)
VIRUSTOTAL_API_KEY = os.getenv('VIRUSTOTAL_API_KEY', '')
GOOGLE_SAFE_BROWSING_KEY = os.getenv('GOOGLE_SAFE_BROWSING_KEY', '')
ABUSEIPDB_API_KEY = os.getenv('ABUSEIPDB_API_KEY', '')

class ValidadorAPIs:
    """Servicio para validar URLs con múltiples APIs de ciberseguridad"""
    
    @staticmethod
    def validar_virustotal(url: str) -> Dict[str, Any]:
        """Consulta VirusTotal para verificar si una URL es maliciosa"""
        if not VIRUSTOTAL_API_KEY:
            return {"error": "API Key no configurada", "servicio": "VirusTotal"}
        
        try:
            # URL para escanear
            scan_url = "https://www.virustotal.com/api/v3/urls"
            headers = {
                "x-apikey": VIRUSTOTAL_API_KEY
            }
            
            # Enviar URL para análisis
            data = {"url": url}
            response = requests.post(scan_url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                analysis_id = result.get('data', {}).get('id', '')
                
                # Obtener resultado del análisis
                if analysis_id:
                    analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
                    analysis_response = requests.get(analysis_url, headers=headers, timeout=10)
                    
                    if analysis_response.status_code == 200:
                        data = analysis_response.json()
                        stats = data.get('data', {}).get('attributes', {}).get('stats', {})
                        
                        return {
                            "servicio": "VirusTotal",
                            "malicioso": stats.get('malicious', 0) > 0,
                            "detecciones": stats.get('malicious', 0),
                            "total_escaneos": sum(stats.values()),
                            "detalles": stats
                        }
            
            return {"error": "No se pudo obtener respuesta", "servicio": "VirusTotal"}
            
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
                    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url}]
                }
            }
            
            response = requests.post(api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                matches = result.get('matches', [])
                
                return {
                    "servicio": "Google Safe Browsing",
                    "malicioso": len(matches) > 0,
                    "amenazas_detectadas": len(matches),
                    "detalles": matches
                }
            
            return {"error": "No se pudo obtener respuesta", "servicio": "Google Safe Browsing"}
            
        except Exception as e:
            return {"error": str(e), "servicio": "Google Safe Browsing"}
    
    @staticmethod
    def validar_abuseipdb(ip: str) -> Dict[str, Any]:
        """Consulta AbuseIPDB para verificar reputación de IP"""
        if not ABUSEIPDB_API_KEY:
            return {"error": "API Key no configurada", "servicio": "AbuseIPDB"}
        
        try:
            url = "https://api.abuseipdb.com/api/v2/check"
            headers = {
                "Key": ABUSEIPDB_API_KEY,
                "Accept": "application/json"
            }
            params = {
                "ipAddress": ip,
                "maxAgeInDays": 90
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                
                return {
                    "servicio": "AbuseIPDB",
                    "malicioso": data.get('abuseConfidenceScore', 0) > 50,
                    "score": data.get('abuseConfidenceScore', 0),
                    "reportes": data.get('totalReports', 0),
                    "detalles": data
                }
            
            return {"error": "No se pudo obtener respuesta", "servicio": "AbuseIPDB"}
            
        except Exception as e:
            return {"error": str(e), "servicio": "AbuseIPDB"}