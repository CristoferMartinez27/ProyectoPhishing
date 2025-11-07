from datetime import datetime

class TakedownService:
    """Servicio para generar solicitudes de takedown"""
    
    @staticmethod
    def generar_asunto(sitio_url: str, cliente_nombre: str) -> str:
        """Genera el asunto del email de takedown"""
        return f"[URGENT] Takedown Request - Phishing Site Impersonating {cliente_nombre}"
    
    @staticmethod
    def generar_cuerpo_email(
        sitio_url: str,
        cliente_nombre: str,
        dominio_legitimo: str,
        ip: str = None,
        notas: str = None
    ) -> str:
        """Genera el cuerpo del email de takedown"""
        
        fecha_actual = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        cuerpo = f"""Dear Abuse Department,

I am writing to report a phishing website that is illegally impersonating {cliente_nombre} ({dominio_legitimo}).

FRAUDULENT WEBSITE DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Phishing URL: {sitio_url}
- Legitimate Domain: {dominio_legitimo}
- Report Date: {fecha_actual}
"""
        
        if ip:
            cuerpo += f"• IP Address: {ip}\n"
        
        cuerpo += f"""
DESCRIPTION OF THE ISSUE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This website is a fraudulent copy designed to deceive users into believing they are 
interacting with {cliente_nombre}'s official website. The site is being used for 
phishing purposes to steal sensitive information from unsuspecting users.

"""
        
        if notas:
            cuerpo += f"""ADDITIONAL INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{notas}

"""
        
        cuerpo += """VALIDATION EVIDENCE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This site has been validated as malicious through multiple security APIs including:
- VirusTotal
- Google Safe Browsing
- AbuseIPDB

REQUESTED ACTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
We kindly request that you take immediate action to:
1. Suspend/terminate the fraudulent website
2. Suspend the hosting account associated with this domain
3. Provide confirmation once the takedown is complete

LEGAL NOTICE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This fraudulent website violates:
- Trademark and copyright laws
- Anti-phishing regulations
- Terms of Service of your hosting platform

CONTACT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For any questions or to provide updates on this case, please contact us at this email address.

Thank you for your prompt attention to this urgent security matter.

Best regards,
PhishGuard Security Team
Anti-Phishing Platform
"""
        
        return cuerpo
    
    @staticmethod
    def obtener_email_abuse(dominio: str) -> str:
        """
        Sugiere el email de abuse basado en el dominio.
        En producción, esto podría hacer una consulta WHOIS real.
        """
        # Emails comunes de abuse
        return f"abuse@{dominio}"
    
    @staticmethod
    def obtener_emails_abuse_comunes() -> list:
        """Retorna una lista de emails de abuse comunes de proveedores"""
        return [
            # --- Grandes Plataformas (Clave para Phishing) ---
            "reportphishing@google.com",        # Google Safe Browsing
            "report@netcraft.com",              # Netcraft
            "reportphishing@apwg.org",          # Anti-Phishing Working Group   

            # --- Proveedores Principales de AV (Correcciones) ---
            "phishing@kaspersky.com",           # Kaspersky
            "phishing@malwarebytes.com",        # Malwarebytes
            "phishing@f-secure.com",            # F-Secure
            
            # --- Correos de Spam/Samples (Aceptan URLs) ---
            "spam@avast.com",                   # Avast / AVG / Lavasoft / Norman
            "spam@avira.com",                   # Avira / Norton 
            "spam@mcafee.com",                  # McAfee 
            "samples@eset.com",                 # ESET 
            "samples@ikarus.at",                # Ikarus
            "v3sos@ahnlab.com",                 # AhnLab
            "virus@nanoav.ru",                  # NANO Antivirus
            "virus.samples@watchguard.com",     # WatchGuard 
            "submit@symantec.com",              # Symantec
            "akacriismartinezy@gmail.com" # Correo personal de pruebas
        ]