from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, usuarios, clientes
from routes import auth, usuarios, clientes, sitios


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
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(sitios.router)

@app.get("/")
def root():
    return {
        "mensaje": "API Plataforma Anti-Phishing",
        "version": "1.0.0",
        "estado": "activo"
    }