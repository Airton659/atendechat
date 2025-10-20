# api/src/atendimento_crewai/main.py - Ponto de entrada principal da nova API CrewAI

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import vertexai
import firebase_admin
from firebase_admin import credentials

# --- INICIALIZAÇÃO EXPLÍCITA E À PROVA DE FALHAS ---

# 1. Encontramos o caminho absoluto para o diretório raiz do projeto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 2. Construímos o caminho absoluto para o arquivo .env que está na raiz
DOTENV_PATH = os.path.join(PROJECT_ROOT, '.env')

# 3. Carregamos o .env a partir de seu caminho exato
print(f"🕵️  Carregando arquivo de ambiente de: {DOTENV_PATH}")
load_dotenv(dotenv_path=DOTENV_PATH)

# 4. Configuração do Firebase Admin SDK com suporte a Workload Identity
if os.environ.get("GOOGLE_CLOUD_PROJECT"):
    # Ambiente de produção (Cloud Run) - usa Workload Identity
    print("🌥️ Detectado ambiente Cloud Run - usando Workload Identity")
    try:
        firebase_admin.initialize_app()
        print("🔥 Firebase Admin SDK inicializado com Workload Identity!")
    except Exception as e:
        print(f"❌ Erro ao inicializar Firebase com Workload Identity: {e}")
else:
    # Ambiente local - usa arquivo de credenciais
    print("🏠 Detectado ambiente local - usando arquivo de credenciais")
    GOOGLE_CREDS_PATH = os.path.join(PROJECT_ROOT, "src", "atendimento_crewai", "google-credentials.json")

    if os.path.exists(GOOGLE_CREDS_PATH):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDS_PATH
        print(f"🔐 Usando credenciais do Google em: {GOOGLE_CREDS_PATH}")

        try:
            cred = credentials.Certificate(GOOGLE_CREDS_PATH)
            firebase_admin.initialize_app(cred)
            print("🔥 Firebase Admin SDK inicializado com arquivo de credenciais!")
        except Exception as e:
            print(f"❌ Erro ao inicializar Firebase com arquivo: {e}")
    else:
        print("❌ Arquivo google-credentials.json não encontrado para desenvolvimento local")
        # Não encerrar em desenvolvimento, permitir continuar sem Firebase para testes
        print("⚠️ Continuando sem Firebase para desenvolvimento/testes")

# 5. Inicializamos o Vertex AI
print(f"🚀 Inicializando VertexAI...")
try:
    # IMPORTANTE: Usar 'global' para modelos Gemini (gemini-2.5-flash-lite, etc)
    # Embeddings vamos inicializar separadamente com região específica
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
    vertexai.init(location=location)
    print(f"✅ VertexAI inicializado com sucesso! Região: {location}")
except Exception as e:
    print(f"❌ Erro ao inicializar VertexAI: {e}")

# --- FIM DA INICIALIZAÇÃO ---

# Os imports da aplicação vêm DEPOIS da inicialização
from atendimento_crewai.main_service import router as main_router

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

# Manter compatibilidade com API v1 (AutoGen)
try:
    from atendimento_autogen.service import router as autogen_router
    app.include_router(autogen_router, prefix="/api/v1", tags=["AutoGen Legacy"])
    print("📦 API v1 (AutoGen) carregada para compatibilidade")
except ImportError as e:
    print(f"⚠️ API v1 (AutoGen) não disponível: {e}")

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

    # Verificar Firebase
    try:
        from firebase_admin import firestore
        db = firestore.client()
        # Teste simples de conectividade
        db.collection('health_check').limit(1).get()
        health_status["services"]["firebase"] = "connected"
    except Exception as e:
        health_status["services"]["firebase"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

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