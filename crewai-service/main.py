# crewai-service/main.py - Ponto de entrada principal da API Architect

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import vertexai

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar Vertex AI
print(f"🚀 Inicializando VertexAI...")
try:
    # Usar 'global' para modelos Gemini
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

    if project_id:
        vertexai.init(project=project_id, location=location)
        print(f"✅ VertexAI inicializado! Projeto: {project_id}, Região: {location}")
    else:
        print("⚠️ GOOGLE_CLOUD_PROJECT não configurado. Usando credenciais padrão...")
        vertexai.init(location=location)
        print(f"✅ VertexAI inicializado com credenciais padrão! Região: {location}")
except Exception as e:
    print(f"❌ Erro ao inicializar VertexAI: {e}")
    print("⚠️ Continuando sem VertexAI - funcionalidade de geração de agentes estará limitada")

# Importar routers
from architect_service import router as architect_router

# Criar aplicação FastAPI
app = FastAPI(
    title="Atendechat - Agent Architect API",
    description="API de Geração Automática de Agentes IA usando Vertex AI (Gemini)",
    version="1.0.0",
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
app.include_router(architect_router, prefix="/api/v2")

@app.get("/")
def read_root():
    return {
        "service": "Atendechat - Agent Architect API",
        "version": "1.0.0",
        "engine": "Vertex AI (Gemini)",
        "status": "online",
        "features": {
            "architect_agent": True,
            "auto_generate_agents": True,
            "industry_templates": True,
            "vertex_ai": True
        },
        "apis": {
            "v2": "/api/v2/architect",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
def health_check():
    """Verificação de saúde"""

    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "services": {}
    }

    # Verificar VertexAI
    try:
        import vertexai
        health_status["services"]["vertex_ai"] = "available"
    except Exception as e:
        health_status["services"]["vertex_ai"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    return health_status

@app.get("/version")
def get_version():
    """Informações de versão"""
    return {
        "api_version": "1.0.0",
        "engine": "Vertex AI (Gemini)",
        "model": os.getenv("VERTEX_MODEL", "gemini-2.5-flash-lite"),
        "python_version": os.sys.version,
        "environment": os.environ.get("NODE_ENV", "development"),
        "features": {
            "auto_generate_agents": True,
            "industry_templates": True,
            "business_analysis": True
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

    port = int(os.environ.get("PORT", 8001))
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
