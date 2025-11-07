from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, usuarios, clientes, sitios, whitelist, takedown, bitacora

app = FastAPI(
    title="Plataforma Anti-Phishing",
    description="Sistema de detección y takedown de sitios fraudulentos",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(sitios.router)
app.include_router(whitelist.router)
app.include_router(takedown.router)
app.include_router(bitacora.router)

@app.get("/")
def root():
    return {
        "mensaje": "API Plataforma Anti-Phishing",
        "version": "1.0.0",
        "estado": "activo",
        "documentacion": "/docs"
    }

@app.get("/health")
def health_check():
    """Endpoint para verificar que el servicio está funcionando"""
    return {
        "status": "healthy",
        "service": "phishing-platform-api"
    }

@app.get("/test-smtp")
def test_smtp_connection():
    """Endpoint para probar la conexión SMTP"""
    from app.services.email_service import EmailService
    
    email_service = EmailService()
    
    # Primero verificar configuración
    if not email_service.verificar_configuracion():
        return {
            "success": False,
            "error": "Configuración SMTP incompleta",
            "smtp_user": email_service.smtp_user or "NO CONFIGURADO",
            "smtp_host": email_service.smtp_host,
            "smtp_port": email_service.smtp_port
        }
    
    # Probar conexión
    result = email_service.test_connection()
    
    return {
        **result,
        "smtp_config": {
            "host": email_service.smtp_host,
            "port": email_service.smtp_port,
            "user": email_service.smtp_user
        }
    }