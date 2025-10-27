# CrewAI Service - Main Entry Point

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import vertexai
import firebase_admin
from firebase_admin import credentials

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar Firebase
creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if creds_path and os.path.exists(creds_path):
    cred = credentials.Certificate(creds_path)
    firebase_admin.initialize_app(cred)
    print(f"✅ Firebase inicializado com credenciais: {creds_path}")
else:
    print("⚠️ Firebase não inicializado - credenciais não encontradas")

# Inicializar Vertex AI
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

if project_id:
    vertexai.init(project=project_id, location=location)
    print(f"✅ Vertex AI inicializado - Projeto: {project_id}, Região: {location}")
else:
    print("⚠️ Vertex AI não inicializado - GOOGLE_CLOUD_PROJECT não definido")

# Importar routers
from atendimento_crewai.main_service import router as main_router
from atendimento_crewai.architect_service import router as architect_router
from atendimento_crewai.training_service import router as training_router
from atendimento_crewai.crews_service import router as crews_router
from atendimento_crewai.knowledge_service import router as knowledge_router

# Criar aplicação FastAPI
app = FastAPI(
    title="CrewAI Service - Atendechat",
    description="Serviço standalone de CrewAI para atendimento com IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers (SEM prefixo - Nginx já roteia)
app.include_router(main_router)
app.include_router(architect_router)
app.include_router(training_router)
app.include_router(crews_router)
app.include_router(knowledge_router)

@app.get("/")
def read_root():
    return {
        "service": "CrewAI Service - Atendechat",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    health = {
        "status": "healthy",
        "services": {}
    }

    # Check Firebase
    try:
        from firebase_admin import firestore
        db = firestore.client()
        db.collection('health_check').limit(1).get()
        health["services"]["firebase"] = "connected"
    except Exception as e:
        health["services"]["firebase"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Check Vertex AI
    try:
        import vertexai
        health["services"]["vertex_ai"] = "configured"
    except Exception as e:
        health["services"]["vertex_ai"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return health

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"🚀 Iniciando CrewAI Service em {host}:{port}")
    print(f"📚 Documentação: http://{host}:{port}/docs")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("NODE_ENV") != "production"
    )
