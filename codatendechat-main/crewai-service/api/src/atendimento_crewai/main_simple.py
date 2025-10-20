# api/src/atendimento_crewai/main_simple.py - Versão simplificada da API

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importações condicionais para evitar erros se as dependências não estiverem instaladas
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase não disponível")

try:
    import vertexai
    VERTEXAI_AVAILABLE = True
except ImportError:
    VERTEXAI_AVAILABLE = False
    print("⚠️ VertexAI não disponível")

# Inicialização do Firebase (se disponível)
if FIREBASE_AVAILABLE:
    try:
        if not firebase_admin._apps:
            # Tentar diferentes caminhos para as credenciais
            cred_paths = [
                "/app/src/atendimento_crewai/google-credentials.json",
                "./google-credentials.json",
                "google-credentials.json"
            ]

            cred_path = None
            for path in cred_paths:
                if os.path.exists(path):
                    cred_path = path
                    break

            if cred_path:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print(f"🔥 Firebase inicializado com {cred_path}")
            else:
                print("⚠️ Arquivo de credenciais não encontrado")
    except Exception as e:
        print(f"⚠️ Erro ao inicializar Firebase: {e}")

# Inicialização do Vertex AI (se disponível)
if VERTEXAI_AVAILABLE:
    try:
        vertexai.init(location=os.getenv("GOOGLE_CLOUD_LOCATION", "global"))
        print("✅ VertexAI inicializado")
    except Exception as e:
        print(f"⚠️ Erro ao inicializar VertexAI: {e}")

# Modelos Pydantic
class ProcessMessageRequest(BaseModel):
    tenantId: str
    crewId: str
    message: str
    conversationHistory: Optional[List[Dict[str, Any]]] = []
    agentOverride: Optional[str] = None

class GenerateTeamRequest(BaseModel):
    businessDescription: str
    industry: Optional[str] = ""
    tenantId: str
    teamName: Optional[str] = ""

# Criar aplicação FastAPI
app = FastAPI(
    title="Atende AI - API v2 (Simplified)",
    description="API simplificada para desenvolvimento e testes",
    version="2.0.0-dev"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ROTAS BÁSICAS ===

@app.get("/")
def read_root():
    return {
        "service": "Atende AI - API v2 (Simplified)",
        "version": "2.0.0-dev",
        "status": "online",
        "firebase": FIREBASE_AVAILABLE,
        "vertexai": VERTEXAI_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "services": {
            "firebase": "available" if FIREBASE_AVAILABLE else "unavailable",
            "vertexai": "available" if VERTEXAI_AVAILABLE else "unavailable"
        },
        "timestamp": datetime.now().isoformat()
    }

# === PROCESSAMENTO DE MENSAGENS ===

@app.post("/process-message")
async def process_message(request: ProcessMessageRequest = Body(...)):
    """
    Processa uma mensagem - versão simplificada para desenvolvimento
    """
    try:
        # Resposta inteligente baseada na mensagem
        message_lower = request.message.lower()

        if any(word in message_lower for word in ['olá', 'oi', 'bom dia', 'boa tarde']):
            response = f"Olá! Sou da equipe {request.crewId}. Como posso ajudá-lo hoje?"
            agent_used = "triagem"
        elif any(word in message_lower for word in ['preço', 'valor', 'quanto custa']):
            response = "Vou consultar nossos preços para você. Pode me dar mais detalhes sobre o que você está procurando?"
            agent_used = "vendas"
        elif any(word in message_lower for word in ['problema', 'erro', 'não funciona']):
            response = "Entendo que você está com um problema. Pode me explicar em detalhes o que está acontecendo?"
            agent_used = "suporte"
        elif any(word in message_lower for word in ['cardápio', 'menu', 'pratos']):
            response = "Nosso cardápio tem várias opções deliciosas! Que tipo de prato você está procurando?"
            agent_used = "cardapio"
        else:
            response = f"Obrigado por sua mensagem sobre '{request.message}'. Como posso ajudá-lo com isso?"
            agent_used = "geral"

        # Simular processamento
        processing_time = 1.2

        return {
            "response": response,
            "agent_used": agent_used,
            "agent_name": f"Agente {agent_used.title()}",
            "tools_used": False,
            "success": True,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "demo_mode": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# === AGENTE ARQUITETO ===

@app.post("/architect/generate-team")
async def generate_team(request: GenerateTeamRequest = Body(...)):
    """
    Gera uma equipe de IA baseada na descrição do negócio - versão simplificada
    """
    try:
        # Análise simples do tipo de negócio
        business_lower = request.businessDescription.lower()

        # Determinar setor se não especificado
        if not request.industry:
            if any(word in business_lower for word in ['imóvel', 'casa', 'apartamento', 'aluguel']):
                industry = 'imobiliaria'
            elif any(word in business_lower for word in ['restaurante', 'comida', 'cardápio']):
                industry = 'restaurante'
            elif any(word in business_lower for word in ['loja', 'produto', 'venda']):
                industry = 'e-commerce'
            elif any(word in business_lower for word in ['médico', 'clínica', 'consulta']):
                industry = 'saude'
            else:
                industry = 'geral'
        else:
            industry = request.industry

        # Gerar blueprint baseado no setor
        blueprint = _generate_blueprint_for_industry(industry, request.businessDescription)
        blueprint["tenantId"] = request.tenantId
        blueprint["name"] = request.teamName or f"Equipe {industry.title()}"

        return {
            "blueprint": blueprint,
            "analysis": {
                "industry": industry,
                "agent_count": len(blueprint["agents"]),
                "detected_complexity": "simples" if len(blueprint["agents"]) <= 3 else "médio"
            },
            "suggestions": [
                "Revise os agentes gerados e personalize conforme necessário",
                "Adicione conhecimento específico da sua empresa",
                "Teste a equipe com cenários reais"
            ],
            "success": True
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# === OUTRAS ROTAS ===

@app.get("/crews/{tenant_id}/{crew_id}/agents")
async def get_crew_agents(tenant_id: str, crew_id: str):
    """
    Retorna agentes disponíveis - versão demo
    """
    demo_agents = [
        {
            'id': 'triagem',
            'name': 'Agente de Triagem',
            'role': 'Especialista em classificação',
            'goal': 'Entender a necessidade do cliente',
            'tools': [],
            'order': 1
        },
        {
            'id': 'vendas',
            'name': 'Agente de Vendas',
            'role': 'Consultor comercial',
            'goal': 'Apresentar produtos e conduzir vendas',
            'tools': ['consultar_base_conhecimento'],
            'order': 2
        },
        {
            'id': 'suporte',
            'name': 'Agente de Suporte',
            'role': 'Especialista em atendimento',
            'goal': 'Resolver problemas e dúvidas',
            'tools': ['consultar_base_conhecimento'],
            'order': 3
        }
    ]

    return {
        "agents": demo_agents,
        "total": len(demo_agents),
        "crew_id": crew_id
    }

@app.get("/capabilities")
async def get_capabilities():
    """
    Retorna capacidades da API
    """
    return {
        "features": {
            "crew_ai": VERTEXAI_AVAILABLE,
            "knowledge_base": FIREBASE_AVAILABLE,
            "interactive_training": True,
            "architect_agent": True,
            "vector_search": False,  # Simplificado
            "multi_tenant": True
        },
        "supported_tools": [
            "consultar_base_conhecimento"
        ],
        "supported_file_types": [
            "pdf", "docx", "txt"
        ],
        "llm_models": [
            "gemini-pro"
        ]
    }

# === FUNÇÕES AUXILIARES ===

def _generate_blueprint_for_industry(industry: str, description: str) -> Dict[str, Any]:
    """Gera blueprint básico para um setor"""

    base_blueprint = {
        "name": "",
        "description": description,
        "status": "draft",
        "version": "2.0",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "config": {
            "industry": industry,
            "objective": description,
            "tone": "friendly",
            "language": "pt-BR"
        },
        "agents": {},
        "workflow": {
            "entryPoint": "triagem",
            "fallbackAgent": "geral"
        }
    }

    # Agentes básicos por setor
    if industry == 'imobiliaria':
        base_blueprint["agents"] = {
            "triagem": {
                "name": "Agente de Triagem",
                "role": "especialista em qualificação de leads",
                "goal": "identificar o tipo de cliente e sua necessidade imobiliária",
                "backstory": "Especialista em entender necessidades imobiliárias",
                "tools": [],
                "isActive": True,
                "order": 1
            },
            "vendas": {
                "name": "Consultor Imobiliário",
                "role": "especialista em vendas imobiliárias",
                "goal": "apresentar imóveis adequados e agendar visitas",
                "backstory": "Consultor experiente em mercado imobiliário",
                "tools": ["consultar_base_conhecimento"],
                "isActive": True,
                "order": 2
            }
        }
    elif industry == 'restaurante':
        base_blueprint["agents"] = {
            "triagem": {
                "name": "Atendente de Recepção",
                "role": "especialista em atendimento gastronômico",
                "goal": "receber clientes e entender suas preferências",
                "backstory": "Atendente experiente em restaurantes",
                "tools": [],
                "isActive": True,
                "order": 1
            },
            "cardapio": {
                "name": "Especialista em Cardápio",
                "role": "consultor gastronômico",
                "goal": "apresentar pratos e ajudar na escolha",
                "backstory": "Conhece todos os pratos do restaurante",
                "tools": ["consultar_base_conhecimento"],
                "isActive": True,
                "order": 2
            }
        }
    else:
        # Blueprint genérico
        base_blueprint["agents"] = {
            "triagem": {
                "name": "Agente de Triagem",
                "role": "especialista em atendimento",
                "goal": "entender a necessidade do cliente",
                "backstory": "Atendente experiente",
                "tools": [],
                "isActive": True,
                "order": 1
            },
            "geral": {
                "name": "Atendente Geral",
                "role": "assistente generalista",
                "goal": "atender dúvidas e fornecer informações",
                "backstory": "Atendente versátil",
                "tools": ["consultar_base_conhecimento"],
                "isActive": True,
                "order": 2
            }
        }

    return base_blueprint

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"🚀 Iniciando API simplificada em {host}:{port}")

    uvicorn.run(
        "main_simple:app",
        host=host,
        port=port,
        reload=True
    )