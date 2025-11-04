# api/src/atendimento_crewai/main.py - Ponto de entrada principal da nova API CrewAI

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import vertexai

# --- INICIALIZAÇÃO ---

# Carregar .env
load_dotenv()
print(f"🕵️  Carregando variáveis de ambiente...")

# Inicializar Vertex AI
print(f"🚀 Inicializando VertexAI...")
try:
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")

    if project:
        vertexai.init(project=project, location=location)
        print(f"✅ VertexAI inicializado! Projeto: {project}, Região: {location}")
    else:
        print("⚠️ GOOGLE_CLOUD_PROJECT não definido - continuando sem Vertex AI")
except Exception as e:
    print(f"❌ Erro ao inicializar VertexAI: {e}")
    print("⚠️ Continuando sem Vertex AI - sistema pode funcionar com limitações")

# --- FIM DA INICIALIZAÇÃO ---

# Imports dos routers
from main_service import router as main_router
from architect_service import router as architect_router

# Criar aplicação FastAPI
app = FastAPI(
    title="Atende AI - CrewAI API",
    description="API de Atendimento Multi-Tenant com IA Personalizável usando CrewAI",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(main_router, prefix="/api/v2")
app.include_router(architect_router, prefix="/api/v2")

@app.get("/")
def read_root():
    return {
        "service": "Atende AI - Plataforma SaaS de Atendimento Multi-Tenant",
        "version": "2.0.0",
        "engine": "CrewAI",
        "status": "online",
        "features": {
            "crew_ai": True,
            "architect_agent": True,
            "knowledge_base": True,
            "interactive_training": True,
            "multi_tenant": True,
            "vector_search": True
        },
        "apis": {
            "v2_crewai": "/api/v2",
            "v1_autogen_legacy": "/api/v1",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
def health_check():
    """Verificação de saúde detalhada"""

    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # Será atualizado automaticamente
        "version": "2.0.0",
        "services": {}
    }

    # Verificar VertexAI
    try:
        import vertexai
        health_status["services"]["vertex_ai"] = "available"
    except Exception as e:
        health_status["services"]["vertex_ai"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Verificar CrewAI
    try:
        import crewai
        health_status["services"]["crew_ai"] = "available"
    except Exception as e:
        health_status["services"]["crew_ai"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    return health_status

@app.get("/version")
def get_version():
    """Informações de versão detalhadas"""
    return {
        "api_version": "2.0.0",
        "engine": "CrewAI",
        "python_version": os.sys.version,
        "environment": os.environ.get("NODE_ENV", "development"),
        "features": {
            "multi_tenant": True,
            "rbac": True,
            "vector_search": True,
            "interactive_training": True,
            "architect_agent": True,
            "knowledge_management": True,
            "real_time_chat": True
        },
        "breaking_changes": [
            "API v2 usa CrewAI em vez de AutoGen",
            "Novos endpoints para gerenciamento de equipes",
            "Sistema de treinamento interativo redesenhado",
            "Base de conhecimento com busca vetorial"
        ],
        "migration": {
            "from_v1": "Use o endpoint /api/v2/migrate-from-autogen",
            "documentation": "/docs"
        }
    }

# Manipulador de erros global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Tratamento global de exceções"""
    import traceback
    from fastapi.responses import JSONResponse

    print(f"❌ Erro não tratado: {exc}")
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "message": "Ocorreu um erro inesperado. Contate o suporte se o problema persistir.",
            "type": type(exc).__name__,
            "request_path": str(request.url.path)
        }
    )

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"🚀 Iniciando servidor em {host}:{port}")
    print(f"📚 Documentação disponível em: http://{host}:{port}/docs")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.environ.get("NODE_ENV") != "production",
        log_level="info"
    )
# Incluir router de knowledge base
from knowledge_service_router import router as knowledge_router
app.include_router(knowledge_router, prefix="/api/v2")
