# api/src/atendimento_crewai/architect.py - Agente Arquiteto para Geração Automática de Equipes

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
    e gerar automaticamente uma equipe de IA personalizada.
    """

    def __init__(self):
        self.model_name = os.getenv("VERTEX_MODEL", "gemini-2.5-flash-lite")
        self.model = GenerativeModel(self.model_name)

        # Templates base para diferentes setores
        self.industry_templates = {
            "imobiliaria": {
                "agents": ["triagem", "vendas", "suporte", "agendamento"],
                "focus": "qualificação de leads e agendamento de visitas",
                "tone": "professional"
            },
            "restaurante": {
                "agents": ["triagem", "cardapio", "pedidos", "suporte"],
                "focus": "atendimento ao cliente e gestão de pedidos",
                "tone": "friendly"
            },
            "e-commerce": {
                "agents": ["triagem", "vendas", "suporte", "pos_venda"],
                "focus": "vendas online e suporte ao cliente",
                "tone": "professional"
            },
            "saude": {
                "agents": ["triagem", "agendamento", "suporte", "emergencia"],
                "focus": "agendamento de consultas e suporte médico",
                "tone": "professional"
            },
            "educacao": {
                "agents": ["triagem", "informacoes", "matriculas", "suporte"],
                "focus": "informações sobre cursos e matrículas",
                "tone": "friendly"
            },
            "servicos": {
                "agents": ["triagem", "orcamento", "agendamento", "suporte"],
                "focus": "orçamentos e agendamento de serviços",
                "tone": "professional"
            },
            "tecnologia": {
                "agents": ["triagem", "suporte_tecnico", "vendas", "desenvolvimento"],
                "focus": "suporte técnico e vendas de soluções",
                "tone": "technical"
            }
        }

    def analyze_business(self, description: str) -> BusinessContext:
        """Analisa a descrição do negócio e extrai contexto estruturado"""

        prompt = f"""
        Analise a seguinte descrição de negócio e extraia informações estruturadas:

        Descrição: "{description}"

        Retorne um JSON com:
        {{
            "industry": "categoria do setor (imobiliaria, restaurante, e-commerce, saude, educacao, servicos, tecnologia, outro)",
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
            analysis = json.loads(response.text.strip())

            return BusinessContext(
                description=description,
                industry=analysis.get("industry", "outro"),
                size=analysis.get("size", "pequeno"),
                target_audience=analysis.get("target_audience", ""),
                main_goals=analysis.get("main_goals", [])
            )
        except Exception as e:
            print(f"Erro na análise do negócio: {e}")
            return BusinessContext(description=description, industry="outro")

    def generate_team_blueprint(self, business_context: BusinessContext) -> Dict[str, Any]:
        """Gera o blueprint completo da equipe baseado no contexto do negócio"""

        # Usar template base se disponível
        base_template = self.industry_templates.get(business_context.industry, {})

        prompt = f"""
        Você é um especialista em criação de equipes de atendimento automatizado via WhatsApp.

        Contexto do Negócio:
        - Descrição: {business_context.description}
        - Setor: {business_context.industry}
        - Público-alvo: {business_context.target_audience}
        - Objetivos: {', '.join(business_context.main_goals)}

        Crie uma equipe de agentes de IA otimizada para este negócio. Retorne um JSON com esta estrutura:

        {{
            "name": "Nome sugerido para a equipe",
            "description": "Descrição da equipe",
            "config": {{
                "industry": "{business_context.industry}",
                "objective": "objetivo principal da equipe",
                "tone": "professional/friendly/casual/technical",
                "language": "pt-BR"
            }},
            "agents": {{
                "agente_key": {{
                    "name": "Nome do Agente",
                    "role": "papel específico",
                    "goal": "objetivo claro e específico",
                    "backstory": "história/experiência do agente",
                    "personality": {{
                        "tone": "tom de voz",
                        "traits": ["característica1", "característica2"],
                        "customInstructions": "instruções específicas de comportamento"
                    }},
                    "tools": ["ferramenta1", "ferramenta2"],
                    "isActive": true,
                    "order": 1
                }}
            }},
            "workflow": {{
                "entryPoint": "agente_que_recebe_primeiro",
                "fallbackAgent": "agente_padrao",
                "escalationRules": []
            }}
        }}

        Diretrizes:
        1. Crie 3-5 agentes especializados
        2. Sempre inclua um agente de triagem como ponto de entrada
        3. Personalize cada agente para o setor específico
        4. Use tom apropriado para o tipo de negócio
        5. Seja específico nas instruções de personalidade
        6. Inclua ferramentas relevantes (consultar_base_conhecimento, etc.)

        Retorne APENAS o JSON válido, sem explicações.
        """

        try:
            response = self.model.generate_content(prompt)

            # LINHA DE CORREÇÃO CRÍTICA: Verifica se a resposta do modelo não está vazia
            if not response.text or not response.text.strip():
                # Se a resposta for vazia, levanta um erro em vez de quebrar o json.loads
                raise ValueError("A resposta do modelo de IA para geração de blueprint veio vazia.")

            # ================================================================
            # CORREÇÃO DEFINITIVA: Limpa o lixo de Markdown da resposta da IA
            # ================================================================
            cleaned_json_str = response.text.strip()
            if cleaned_json_str.startswith("```json"):
                cleaned_json_str = cleaned_json_str[7:-4].strip()
            elif cleaned_json_str.startswith("```"):
                cleaned_json_str = cleaned_json_str[3:-3].strip()

            blueprint = json.loads(cleaned_json_str)
            # ================================================================


            # Validar e ajustar o blueprint
            blueprint = self._validate_and_enhance_blueprint(blueprint, business_context)

            return blueprint

        except json.JSONDecodeError as json_error:
            print(f"Erro de decodificação JSON na geração do blueprint: {json_error}")
            print(f"Resposta recebida que causou o erro: {response.text}")
            # Lança a exceção para ser capturada pelo serviço e retornar um erro 500
            raise ValueError(f"O modelo de IA retornou um JSON inválido: {response.text}") from json_error
            
        except Exception as e:
            # A exceção agora será mais clara, vindo do nosso "raise ValueError"
            print(f"Erro na geração do blueprint: {e}")
            # Lança a exceção para que o endpoint retorne um erro 500, e não 200 OK.
            raise e

    def _validate_and_enhance_blueprint(self, blueprint: Dict[str, Any], context: BusinessContext) -> Dict[str, Any]:
        """Valida e melhora o blueprint gerado"""

        # Garantir estrutura mínima
        if "agents" not in blueprint:
            blueprint["agents"] = {}

        if "workflow" not in blueprint:
            blueprint["workflow"] = {}

        # Garantir agente de triagem
        if not any("triagem" in key.lower() for key in blueprint["agents"].keys()):
            blueprint["agents"]["triagem"] = self._get_triagem_agent()

        # Garantir agente padrão/geral
        if not any(key in ["geral", "padrao", "suporte"] for key in blueprint["agents"].keys()):
            blueprint["agents"]["geral"] = self._get_default_agent()

        # Definir workflow padrão
        if not blueprint["workflow"].get("entryPoint"):
            # Procurar agente de triagem
            for key in blueprint["agents"].keys():
                if "triagem" in key.lower():
                    blueprint["workflow"]["entryPoint"] = key
                    break

        if not blueprint["workflow"].get("fallbackAgent"):
            # Procurar agente geral/padrão
            for key in blueprint["agents"].keys():
                if key in ["geral", "padrao", "suporte"]:
                    blueprint["workflow"]["fallbackAgent"] = key
                    break

        # Garantir ordem correta dos agentes
        order = 1
        for agent in blueprint["agents"].values():
            if "order" not in agent:
                agent["order"] = order
                order += 1

        return blueprint

    def _get_triagem_agent(self) -> Dict[str, Any]:
        """Retorna agente de triagem padrão"""
        return {
            "name": "Agente de Triagem",
            "role": "especialista em classificação de intenções",
            "goal": "identificar rapidamente a necessidade do cliente e encaminhar para o especialista correto",
            "backstory": "Você é um assistente experiente em atendimento ao cliente, com habilidade especial para entender intenções e fazer encaminhamentos precisos.",
            "personality": {
                "tone": "friendly",
                "traits": ["empático", "eficiente", "organizado"],
                "customInstructions": "Sempre cumprimente o cliente educadamente e faça perguntas objetivas para entender sua necessidade."
            },
            "tools": [],
            "isActive": True,
            "order": 1
        }

    def _get_default_agent(self) -> Dict[str, Any]:
        """Retorna agente padrão/geral"""
        return {
            "name": "Atendente Geral",
            "role": "atendente generalista",
            "goal": "atender dúvidas gerais e fornecer informações básicas sobre a empresa",
            "backstory": "Você é um atendente versátil que conhece bem a empresa e pode ajudar com informações gerais.",
            "personality": {
                "tone": "friendly",
                "traits": ["prestativo", "informativo", "acessível"],
                "customInstructions": "Seja sempre educado e prestativo. Se não souber algo, encaminhe para um especialista."
            },
            "tools": ["consultar_base_conhecimento"],
            "isActive": True,
            "order": 99
        }

    def _get_fallback_blueprint(self, context: BusinessContext) -> Dict[str, Any]:
        """Retorna blueprint básico em caso de falha"""
        return {
            "name": f"Equipe de Atendimento - {context.industry.title()}",
            "description": context.description,
            "config": {
                "industry": context.industry,
                "objective": "Atendimento geral ao cliente",
                "tone": "friendly",
                "language": "pt-BR"
            },
            "agents": {
                "triagem": self._get_triagem_agent(),
                "geral": self._get_default_agent()
            },
            "workflow": {
                "entryPoint": "triagem",
                "fallbackAgent": "geral",
                "escalationRules": []
            }
        }

    def suggest_improvements(self, current_blueprint: Dict[str, Any], performance_data: Dict[str, Any] = None) -> List[str]:
        """Sugere melhorias baseadas no blueprint atual e dados de performance"""

        suggestions = []

        # Analisar estrutura atual
        agents_count = len(current_blueprint.get("agents", {}))

        if agents_count < 3:
            suggestions.append("Considere adicionar mais agentes especializados para melhor atendimento")

        if agents_count > 8:
            suggestions.append("Muitos agentes podem confundir o fluxo. Considere consolidar alguns papéis")

        # Verificar ferramentas
        agents_with_tools = sum(1 for agent in current_blueprint.get("agents", {}).values()
                               if agent.get("tools") and len(agent["tools"]) > 0)

        if agents_with_tools == 0:
            suggestions.append("Adicione ferramentas (como consulta à base de conhecimento) aos agentes")

        # Sugestões baseadas em performance (se disponível)
        if performance_data:
            if performance_data.get("avg_response_time", 0) > 30:
                suggestions.append("Tempo de resposta alto. Considere simplificar o fluxo de decisão")

            if performance_data.get("satisfaction_rate", 1) < 0.7:
                suggestions.append("Taxa de satisfação baixa. Revise as instruções de personalidade dos agentes")

        return suggestions

    def adapt_for_industry(self, base_blueprint: Dict[str, Any], industry: str) -> Dict[str, Any]:
        """Adapta um blueprint genérico para um setor específico"""

        industry_adaptations = {
            "restaurante": {
                "additional_agents": {
                    "cardapio": {
                        "name": "Especialista em Cardápio",
                        "role": "consultor de cardápio e pedidos",
                        "goal": "ajudar clientes a escolher pratos e fazer pedidos",
                        "tools": ["consultar_cardapio", "calcular_preco"]
                    }
                },
                "workflow_changes": {
                    "escalationRules": ["pedido -> cardapio", "duvida_prato -> cardapio"]
                }
            },
            "imobiliaria": {
                "additional_agents": {
                    "vendas": {
                        "name": "Consultor Imobiliário",
                        "role": "especialista em vendas de imóveis",
                        "goal": "qualificar leads e agendar visitas",
                        "tools": ["consultar_imoveis", "agendar_visita"]
                    }
                }
            }
        }

        adaptations = industry_adaptations.get(industry, {})

        # Aplicar adaptações
        if "additional_agents" in adaptations:
            base_blueprint["agents"].update(adaptations["additional_agents"])

        if "workflow_changes" in adaptations:
            base_blueprint["workflow"].update(adaptations["workflow_changes"])

        return base_blueprint