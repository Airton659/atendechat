# crewai-service/architect.py - Agente Arquiteto para Geração Automática de Agentes

import vertexai
from vertexai.generative_models import GenerativeModel
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class BusinessContext:
    description: str
    industry: str
    size: str = "pequeno"  # pequeno, médio, grande
    target_audience: str = ""
    main_goals: List[str] = None

    def __post_init__(self):
        if self.main_goals is None:
            self.main_goals = []

class ArchitectAgent:
    """
    Agente Arquiteto responsável por analisar a descrição do negócio
    e gerar automaticamente agentes de IA personalizados.
    """

    def __init__(self):
        self.model_name = os.getenv("VERTEX_MODEL", "gemini-2.5-flash-lite")
        self.model = GenerativeModel(self.model_name)

        # Templates base para diferentes setores
        self.industry_templates = {
            "ecommerce": {
                "agents": ["triagem", "vendas", "suporte", "pos_venda"],
                "focus": "vendas online e suporte ao cliente",
                "tone": "professional"
            },
            "services": {
                "agents": ["triagem", "orcamento", "agendamento", "suporte"],
                "focus": "orçamentos e agendamento de serviços",
                "tone": "professional"
            },
            "technology": {
                "agents": ["triagem", "suporte_tecnico", "vendas", "desenvolvimento"],
                "focus": "suporte técnico e vendas de soluções",
                "tone": "technical"
            },
            "health": {
                "agents": ["triagem", "agendamento", "suporte", "emergencia"],
                "focus": "agendamento de consultas e suporte médico",
                "tone": "professional"
            },
            "education": {
                "agents": ["triagem", "informacoes", "matriculas", "suporte"],
                "focus": "informações sobre cursos e matrículas",
                "tone": "friendly"
            },
            "finance": {
                "agents": ["triagem", "consultoria", "suporte", "cobranca"],
                "focus": "consultoria financeira e suporte",
                "tone": "professional"
            },
            "retail": {
                "agents": ["triagem", "vendas", "estoque", "suporte"],
                "focus": "vendas e gestão de estoque",
                "tone": "friendly"
            },
            "real_estate": {
                "agents": ["triagem", "vendas", "agendamento", "suporte"],
                "focus": "qualificação de leads e agendamento de visitas",
                "tone": "professional"
            },
            "other": {
                "agents": ["triagem", "atendimento", "suporte"],
                "focus": "atendimento geral ao cliente",
                "tone": "friendly"
            }
        }

    def analyze_business(self, description: str, industry: str = "") -> BusinessContext:
        """Analisa a descrição do negócio e extrai contexto estruturado"""

        # Se a indústria já foi fornecida, usar ela
        if industry and industry in self.industry_templates:
            return BusinessContext(
                description=description,
                industry=industry,
                size="médio",
                target_audience="clientes",
                main_goals=["atendimento eficiente", "satisfação do cliente"]
            )

        prompt = f"""
        Analise a seguinte descrição de negócio e extraia informações estruturadas:

        Descrição: "{description}"

        Retorne um JSON com:
        {{
            "industry": "categoria do setor (ecommerce, services, technology, health, education, finance, retail, real_estate, other)",
            "size": "tamanho estimado (pequeno, médio, grande)",
            "target_audience": "público-alvo principal",
            "main_goals": ["objetivo1", "objetivo2", "objetivo3"],
            "key_services": ["serviço1", "serviço2"],
            "complexity_level": "simples, médio ou complexo"
        }}

        Seja preciso e conciso.
        """

        try:
            response = self.model.generate_content(prompt)

            # Limpar resposta (remover markdown se houver)
            cleaned_json_str = response.text.strip()
            if cleaned_json_str.startswith("```json"):
                cleaned_json_str = cleaned_json_str[7:-3].strip()
            elif cleaned_json_str.startswith("```"):
                cleaned_json_str = cleaned_json_str[3:-3].strip()

            analysis = json.loads(cleaned_json_str)

            return BusinessContext(
                description=description,
                industry=analysis.get("industry", "other"),
                size=analysis.get("size", "pequeno"),
                target_audience=analysis.get("target_audience", ""),
                main_goals=analysis.get("main_goals", [])
            )
        except Exception as e:
            print(f"Erro na análise do negócio: {e}")
            return BusinessContext(description=description, industry=industry or "other")

    def generate_agents_blueprint(self, business_context: BusinessContext) -> List[Dict[str, Any]]:
        """Gera blueprint de agentes baseado no contexto do negócio"""

        prompt = f"""
        Você é um especialista em criação de agentes de IA para atendimento automatizado via WhatsApp.

        Contexto do Negócio:
        - Descrição: {business_context.description}
        - Setor: {business_context.industry}
        - Público-alvo: {business_context.target_audience}
        - Objetivos: {', '.join(business_context.main_goals)}

        Crie uma lista de 3-5 agentes de IA especializados para este negócio. Retorne um JSON com esta estrutura:

        {{
            "agents": [
                {{
                    "name": "Nome do Agente",
                    "function": "função/papel específico (role)",
                    "objective": "objetivo claro e específico (goal)",
                    "backstory": "história/experiência do agente em até 200 caracteres",
                    "keywords": ["palavra1", "palavra2", "palavra3"],
                    "customInstructions": "instruções específicas de comportamento",
                    "persona": "descrição da personalidade",
                    "doList": ["ação1 que o agente DEVE fazer", "ação2"],
                    "dontList": ["ação1 que o agente NÃO DEVE fazer", "ação2"],
                    "isActive": true
                }}
            ]
        }}

        Diretrizes IMPORTANTES:
        1. Crie exatamente 3-5 agentes especializados
        2. Sempre inclua um agente de triagem/atendimento inicial
        3. Use português brasileiro
        4. Seja específico e detalhado
        5. Keywords devem ser palavras-chave que ativam o agente (ex: "orçamento", "preço", "valor")
        6. customInstructions deve ter instruções claras de como o agente deve se comportar
        7. doList: lista de ações que o agente DEVE fazer
        8. dontList: lista de ações que o agente NÃO DEVE fazer
        9. Adapte o tom para o setor: profissional para saúde/finanças, amigável para educação/varejo

        Retorne APENAS o JSON válido, sem explicações ou markdown.
        """

        try:
            response = self.model.generate_content(prompt)

            if not response.text or not response.text.strip():
                raise ValueError("A resposta do modelo de IA veio vazia.")

            # Limpar resposta (remover markdown se houver)
            cleaned_json_str = response.text.strip()
            if cleaned_json_str.startswith("```json"):
                cleaned_json_str = cleaned_json_str[7:-3].strip()
            elif cleaned_json_str.startswith("```"):
                cleaned_json_str = cleaned_json_str[3:-3].strip()

            blueprint = json.loads(cleaned_json_str)

            # Validar e garantir que temos a lista de agentes
            agents = blueprint.get("agents", [])

            if not agents:
                raise ValueError("Nenhum agente foi gerado")

            # Validar cada agente
            for agent in agents:
                if not agent.get("name"):
                    agent["name"] = "Agente sem nome"
                if not agent.get("function"):
                    agent["function"] = "Agente geral"
                if not agent.get("objective"):
                    agent["objective"] = "Auxiliar o cliente"
                if not agent.get("backstory"):
                    agent["backstory"] = "Assistente virtual experiente"
                if not agent.get("keywords"):
                    agent["keywords"] = []
                if not agent.get("customInstructions"):
                    agent["customInstructions"] = "Seja sempre educado e prestativo"
                if not agent.get("persona"):
                    agent["persona"] = "Profissional e atencioso"
                if not agent.get("doList"):
                    agent["doList"] = ["Ser educado", "Ajudar o cliente"]
                if not agent.get("dontList"):
                    agent["dontList"] = ["Ser grosseiro", "Ignorar dúvidas"]
                if "isActive" not in agent:
                    agent["isActive"] = True

            return agents

        except json.JSONDecodeError as json_error:
            print(f"Erro de decodificação JSON: {json_error}")
            print(f"Resposta recebida: {response.text}")
            raise ValueError(f"O modelo de IA retornou um JSON inválido: {response.text}") from json_error

        except Exception as e:
            print(f"Erro na geração de agentes: {e}")
            # Retornar agentes padrão em caso de erro
            return self._get_fallback_agents(business_context)

    def _get_fallback_agents(self, context: BusinessContext) -> List[Dict[str, Any]]:
        """Retorna agentes padrão em caso de falha"""
        return [
            {
                "name": "Atendente Principal",
                "function": "Atendente geral",
                "objective": "Atender e auxiliar clientes com suas necessidades",
                "backstory": "Assistente virtual experiente em atendimento ao cliente",
                "keywords": ["olá", "oi", "help", "ajuda"],
                "customInstructions": "Seja sempre educado, prestativo e profissional. Cumprimente o cliente e pergunte como pode ajudar.",
                "persona": "Profissional, educado e atencioso",
                "doList": ["Cumprimentar educadamente", "Identificar necessidade do cliente", "Fornecer informações claras"],
                "dontList": ["Ser grosseiro", "Ignorar dúvidas", "Fornecer informações incorretas"],
                "isActive": True
            },
            {
                "name": "Suporte Técnico",
                "function": "Especialista em suporte",
                "objective": "Resolver problemas e tirar dúvidas técnicas",
                "backstory": "Especialista em resolver problemas e auxiliar com questões técnicas",
                "keywords": ["problema", "erro", "bug", "não funciona", "ajuda"],
                "customInstructions": "Seja paciente e explique de forma clara. Faça perguntas para entender o problema.",
                "persona": "Paciente, técnico e didático",
                "doList": ["Entender o problema", "Fornecer soluções claras", "Acompanhar até resolução"],
                "dontList": ["Ser impaciente", "Usar termos muito técnicos", "Desistir facilmente"],
                "isActive": True
            }
        ]
