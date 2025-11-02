# crewai-service/main_simple.py - Versão simples sem dependência do Vertex AI

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Carregar variáveis de ambiente
load_dotenv()

print("🤖 Iniciando Architect API (Simple Mode - sem IA generativa)")
print("📦 Usando templates pré-definidos por indústria")

# Importar routers da versão simples
from architect_service_simple import router as architect_router

# Criar aplicação FastAPI
app = FastAPI(
    title="Atendechat - Agent Architect API (Simple)",
    description="API de Geração Automática de Agentes usando Templates Pré-definidos",
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
        "service": "Atendechat - Agent Architect API (Simple)",
        "version": "1.0.0",
        "engine": "Template-Based (No AI)",
        "status": "online",
        "features": {
            "architect_agent": True,
            "auto_generate_agents": True,
            "industry_templates": True,
            "vertex_ai": False
        },
        "apis": {
            "v2": "/api/v2/architect",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "note": "Esta versão usa templates pré-definidos e não requer autenticação do Google Cloud"
    }

@app.get("/health")
def health_check():
    """Verificação de saúde"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "mode": "simple",
        "services": {
            "architect": "available",
            "vertex_ai": "disabled"
        }
    }

@app.get("/version")
def get_version():
    """Informações de versão"""
    return {
        "api_version": "1.0.0",
        "engine": "Template-Based",
        "model": "Pre-defined Templates",
        "python_version": os.sys.version,
        "environment": os.environ.get("NODE_ENV", "development"),
        "features": {
            "auto_generate_agents": True,
            "industry_templates": True,
            "business_analysis": False,
            "ai_generation": False
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
        "main_simple:app",
        host=host,
        port=port,
        reload=os.environ.get("NODE_ENV") != "production",
        log_level="info"
    )
