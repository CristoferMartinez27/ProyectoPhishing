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

@app.get("/test-email")
def test_email_service():
    """Endpoint para probar el servicio de email (SendGrid API)"""
    from app.services.email_service import EmailService
    
    email_service = EmailService()
    
    # Verificar configuración
    if not email_service.verificar_configuracion():
        return {
            "success": False,
            "error": "SENDGRID_API_KEY no está configurada",
            "instrucciones": "Configura SENDGRID_API_KEY en las variables de entorno de Railway"
        }
    
    # Probar configuración
    result = email_service.test_connection()
    
    return result