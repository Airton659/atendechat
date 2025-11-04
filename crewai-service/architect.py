# architect.py - Agente Arquiteto usando Vertex AI para gerar equipes

import vertexai
from vertexai.generative_models import GenerativeModel
import json
import os
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class BusinessContext:
    description: str
    industry: str
    size: str = "médio"
    target_audience: str = ""
    main_goals: List[str] = None

    def __post_init__(self):
        if self.main_goals is None:
            self.main_goals = []

class ArchitectAgent:
    """
    Agente Arquiteto que usa Vertex AI para gerar equipes personalizadas
    """

    def __init__(self):
        self.model_name = "gemini-2.0-flash-lite"
        try:
            self.model = GenerativeModel(self.model_name)
            print(f"✅ Architect Agent inicializado com modelo: {self.model_name}")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar modelo Vertex AI: {e}")
            self.model = None

    def generate_team_name(self, business_context: BusinessContext) -> str:
        """Gera um nome criativo para a equipe baseado no negócio"""

        if not self.model:
            return "Equipe de Atendimento"

        prompt = f"""
Crie um nome criativo e profissional para uma equipe de atendimento via WhatsApp.

Descrição do negócio: {business_context.description}
Setor: {business_context.industry}

Retorne APENAS o nome da equipe, sem explicações. Exemplos de bons nomes:
- "Equipe Saúde Premium"
- "Time Atendimento Imobiliário"
- "Assistentes Clínica Veterinária"
- "Equipe Suporte Tech"

Nome da equipe:"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.8,
                    "max_output_tokens": 50,
                }
            )
            
            team_name = response.text.strip()
            # Remover aspas se houver
            team_name = team_name.strip('"').strip("'")
            return team_name

        except Exception as e:
            print(f"[Architect AI] Erro ao gerar nome: {e}")
            return "Equipe de Atendimento"

    def generate_team_blueprint(self, business_context: BusinessContext) -> Dict[str, Any]:
        """Gera blueprint da equipe usando IA"""

        if not self.model:
            print("⚠️ Modelo não disponível, retornando equipe padrão")
            return self._generate_fallback_team(business_context)

        prompt = f"""
Você é um especialista em criação de equipes de atendimento via WhatsApp.

Contexto do Negócio:
- Descrição: {business_context.description}
- Setor: {business_context.industry}

Crie uma equipe de 3 a 5 agentes especializados para este negócio.

IMPORTANTE: Retorne EXATAMENTE neste formato JSON (sem markdown, sem ```json):

{{
  "agents": [
    {{
      "name": "Nome do Agente",
      "function": "Função/Papel do agente",
      "objective": "Objetivo claro e específico",
      "backstory": "História e experiência do agente em 2-3 frases",
      "keywords": ["palavra1", "palavra2", "palavra3"],
      "customInstructions": "Instruções específicas de como deve atender",
      "persona": "Descrição da personalidade (profissional/amigável/técnico)",
      "doList": ["Faça isso", "Faça aquilo"],
      "dontList": ["Não faça isso", "Não faça aquilo"],
      "isActive": true
    }}
  ],
  "customTools": []
}}

Crie agentes relevantes para o setor. Cada agente deve ter palavras-chave específicas que acionam sua atuação.
Por exemplo: agente de vendas tem palavras como "preço", "comprar", "orçamento".
"""

        try:
            print(f"[Architect AI] Gerando equipe com IA para: {business_context.industry}")

            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                }
            )

            # Extrair JSON da resposta
            response_text = response.text.strip()

            # Remover markdown se houver
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            blueprint = json.loads(response_text)

            print(f"[Architect AI] ✅ Gerados {len(blueprint.get('agents', []))} agentes com IA")

            return blueprint

        except Exception as e:
            print(f"[Architect AI] ❌ Erro ao gerar com IA: {e}")
            print(f"[Architect AI] Usando equipe padrão como fallback")
            return self._generate_fallback_team(business_context)

    def _generate_fallback_team(self, business_context: BusinessContext) -> Dict[str, Any]:
        """Gera equipe padrão caso a IA falhe"""
        
        return {
            "agents": [
                {
                    "name": "Assistente de Atendimento",
                    "function": "Assistente de Atendimento Geral",
                    "objective": "Fornecer atendimento inicial e direcionar clientes",
                    "backstory": "Sou especialista em atendimento ao cliente com foco em resolver dúvidas rapidamente.",
                    "keywords": ["olá", "oi", "ajuda", "informação", "dúvida"],
                    "customInstructions": "Seja cordial e prestativo. Identifique a necessidade do cliente.",
                    "persona": "Profissional e amigável",
                    "doList": ["Cumprimentar cordialmente", "Identificar necessidades", "Direcionar adequadamente"],
                    "dontList": ["Ser impaciente", "Dar informações incorretas"],
                    "isActive": True
                },
                {
                    "name": "Agente de Suporte",
                    "function": "Especialista em Suporte",
                    "objective": "Resolver problemas e dúvidas técnicas",
                    "backstory": "Tenho vasta experiência em resolver problemas e ajudar clientes a superarem desafios.",
                    "keywords": ["problema", "erro", "não funciona", "ajuda", "suporte"],
                    "customInstructions": "Seja paciente e metódico ao resolver problemas.",
                    "persona": "Técnico e paciente",
                    "doList": ["Investigar o problema", "Oferecer soluções", "Testar resoluções"],
                    "dontList": ["Culpar o cliente", "Desistir facilmente"],
                    "isActive": True
                }
            ],
            "customTools": []
        }

    def suggest_improvements(self, current_blueprint: Dict[str, Any], performance_data: Dict[str, Any] = None) -> List[str]:
        """Sugere melhorias para o blueprint atual"""

        suggestions = [
            "Adicione palavras-chave mais específicas para cada agente",
            "Revise o backstory para torná-lo mais alinhado ao negócio",
            "Teste os agentes com cenários reais de atendimento",
            "Ajuste a persona conforme o feedback dos clientes"
        ]

        return suggestions
