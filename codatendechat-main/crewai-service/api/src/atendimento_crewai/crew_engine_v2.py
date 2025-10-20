# api/src/atendimento_crewai/crew_engine_v2.py - Engine CrewAI Atualizada

from crewai import Agent, Task, Crew
from crewai.tools import tool
from langchain_google_vertexai import VertexAI
from typing import Dict, Any, List, Optional
import os
import json
from firebase_admin import firestore
import asyncio

# Importar ferramentas do módulo tools
from atendimento_crewai.tools import (
    cadastrar_cliente_planilha,
    coletar_info_agendamento
)

# Ferramenta para buscar na base de conhecimento
@tool
def consultar_base_conhecimento(consulta: str, max_results: int = 5) -> str:
    """
    Busca informações na base de conhecimento da empresa.

    Args:
        consulta: Texto da consulta para buscar
        max_results: Número máximo de resultados

    Returns:
        Informações relevantes encontradas na base de conhecimento
    """
    try:
        # Aqui integraria com o serviço de conhecimento
        # Por enquanto retorna uma resposta de exemplo
        return f"Informações encontradas para '{consulta}': [Dados da base de conhecimento]"
    except Exception as e:
        return f"Erro ao consultar base de conhecimento: {str(e)}"

class CrewEngine:
    """Engine principal para execução de equipes CrewAI - Versão Simplificada"""

    def __init__(self):
        self.llm = VertexAI(
            model_name=os.getenv("VERTEX_MODEL", "gemini-pro"),
            temperature=0.7,
            max_output_tokens=1000
        )
        try:
            self.db = firestore.client()
        except Exception as e:
            print(f"❌ Erro ao inicializar Firestore: {e}")
            self.db = None

    async def load_crew_blueprint(self, tenant_id: str, crew_id: str) -> Dict[str, Any]:
        """Carrega o blueprint da equipe do Firestore"""
        try:
            if not self.db:
                raise Exception("Firestore não inicializado")

            crew_doc = self.db.collection('crew_blueprints').document(crew_id).get()

            if not crew_doc.exists:
                raise Exception(f"Equipe {crew_id} não encontrada")

            crew_data = crew_doc.to_dict()

            if crew_data.get('tenantId') != tenant_id:
                raise Exception("Acesso negado à equipe")

            return crew_data

        except Exception as e:
            raise Exception(f"Erro ao carregar equipe: {str(e)}")

    def _create_agent_from_config(self, agent_key: str, agent_config: Dict[str, Any], tenant_id: str) -> Agent:
        """Cria um agente CrewAI a partir da configuração"""

        # Preparar ferramentas
        tools = []
        agent_tools = agent_config.get('tools', [])

        # Mapeamento de nomes de ferramentas para funções
        available_tools = {
            'consultar_base_conhecimento': consultar_base_conhecimento,
            'cadastrar_cliente_planilha': cadastrar_cliente_planilha,
            'coletar_info_agendamento': coletar_info_agendamento
        }

        # Adicionar ferramentas configuradas
        print(f"🔧 Ferramentas configuradas no agente '{agent_key}': {agent_tools}")
        for tool_name in agent_tools:
            if tool_name in available_tools:
                tools.append(available_tools[tool_name])
                print(f"   ✅ Ferramenta '{tool_name}' adicionada com sucesso")
            else:
                print(f"   ⚠️ Ferramenta '{tool_name}' não encontrada!")

        print(f"📋 Total de ferramentas carregadas: {len(tools)}")

        # Construir backstory personalizado
        personality = agent_config.get('personality', {})
        backstory = agent_config.get('backstory', '')

        if personality:
            tone = personality.get('tone', 'professional')
            traits = personality.get('traits', [])
            custom_instructions = personality.get('customInstructions', '')

            backstory += f"\n\nPersonalidade: Você tem um tom {tone}"
            if traits:
                backstory += f" e é caracterizado por ser {', '.join(traits)}"
            if custom_instructions:
                backstory += f"\n\nInstruções especiais: {custom_instructions}"

        # Adicionar configurações de ferramentas ao backstory
        tool_configs = agent_config.get('toolConfigs', {})
        if tool_configs:
            backstory += "\n\n=== CONFIGURAÇÕES DE FERRAMENTAS ==="

            # Google Sheets
            if 'cadastrar_cliente_planilha' in agent_tools and 'googleSheets' in tool_configs:
                sheets_config = tool_configs['googleSheets']
                backstory += f"\n\nQuando usar a ferramenta cadastrar_cliente_planilha, SEMPRE use:"
                backstory += f"\n- spreadsheet_id: {sheets_config.get('spreadsheetId', '')}"
                backstory += f"\n- range_name: {sheets_config.get('rangeName', 'Clientes!A:E')}"

            # Outras configurações de ferramentas podem ser adicionadas aqui

        # Criar agente
        print(f"\n📝 BACKSTORY FINAL DO AGENTE '{agent_key}':")
        print(f"{backstory.strip()}\n")

        agent = Agent(
            role=agent_config.get('role', 'assistente'),
            goal=agent_config.get('goal', 'ajudar o usuário'),
            backstory=backstory.strip(),
            tools=tools,
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

        return agent

    def _create_task_for_message(self, message: str, agent: Agent, context: str = "") -> Task:
        """Cria uma tarefa CrewAI para processar uma mensagem"""

        description = f"""
        Você recebeu a seguinte mensagem de um cliente: "{message}"

        {context}

        Sua tarefa é:
        1. Analisar a mensagem do cliente
        2. Usar suas ferramentas se necessário para obter informações relevantes
        3. Fornecer uma resposta útil, clara e personalizada
        4. Manter o tom e personalidade definidos no seu perfil

        Responda diretamente ao cliente de forma natural e conversacional.
        """

        task = Task(
            description=description,
            expected_output="Uma resposta clara e útil para o cliente",
            agent=agent
        )

        return task

    async def process_message(
        self,
        tenant_id: str,
        crew_id: str,
        message: str,
        conversation_history: List[Dict[str, Any]] = None,
        agent_override: str = None
    ) -> Dict[str, Any]:
        """Processa uma mensagem usando a equipe CrewAI - Versão Simplificada"""

        try:
            # Para demo, vou criar uma resposta simples sem Firestore
            if not self.db:
                return self._create_demo_response(message, tenant_id, crew_id)

            # Carregar blueprint da equipe
            crew_blueprint = await self.load_crew_blueprint(tenant_id, crew_id)

            # Preparar contexto da conversa
            context = ""
            if conversation_history:
                context = "Histórico da conversa:\n"
                for msg in conversation_history[-5:]:  # Últimas 5 mensagens
                    role = "Cliente" if msg.get('role') == 'user' else "Assistente"
                    context += f"{role}: {msg.get('content', '')}\n"
                context += "\n"

            # Selecionar agente
            selected_agent_key = self._select_agent(crew_blueprint, message, agent_override)
            agent_config = crew_blueprint['agents'][selected_agent_key]

            # Criar agente
            agent = self._create_agent_from_config(selected_agent_key, agent_config, tenant_id)

            # Criar tarefa
            task = self._create_task_for_message(message, agent, context)

            # Criar e executar crew
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=True
            )

            # Executar
            result = crew.kickoff()

            # Processar resultado
            response_text = str(result).strip() if result else "Desculpe, não consegui processar sua solicitação."

            return {
                "response": response_text,
                "agent_used": selected_agent_key,
                "agent_name": agent_config.get('name', selected_agent_key),
                "tools_used": len(agent_config.get('tools', [])) > 0,
                "success": True
            }

        except Exception as e:
            print(f"Erro ao processar mensagem com CrewAI: {e}")
            return {
                "response": "Desculpe, ocorreu um erro interno. Por favor, tente novamente.",
                "agent_used": None,
                "error": str(e),
                "success": False
            }

    def _create_demo_response(self, message: str, tenant_id: str, crew_id: str) -> Dict[str, Any]:
        """Cria uma resposta demo sem depender do Firestore"""

        # Resposta inteligente baseada na mensagem
        message_lower = message.lower()

        if any(word in message_lower for word in ['olá', 'oi', 'bom dia', 'boa tarde']):
            response = "Olá! Como posso ajudá-lo hoje?"
            agent_used = "triagem"
        elif any(word in message_lower for word in ['preço', 'valor', 'quanto custa']):
            response = "Vou consultar nossos preços para você. Pode me dar mais detalhes sobre o que você está procurando?"
            agent_used = "vendas"
        elif any(word in message_lower for word in ['problema', 'erro', 'não funciona']):
            response = "Entendo que você está com um problema. Pode me explicar em detalhes o que está acontecendo para que eu possa ajudá-lo?"
            agent_used = "suporte"
        else:
            response = f"Obrigado por sua mensagem: '{message}'. Como posso ajudá-lo com isso?"
            agent_used = "geral"

        return {
            "response": response,
            "agent_used": agent_used,
            "agent_name": f"Agente {agent_used.title()}",
            "tools_used": False,
            "success": True,
            "demo_mode": True
        }

    def _select_agent(self, crew_blueprint: Dict[str, Any], message: str, agent_override: str = None) -> str:
        """Seleciona qual agente deve processar a mensagem"""

        agents = crew_blueprint.get('agents', {})

        # Se agente específico foi solicitado
        if agent_override and agent_override in agents:
            return agent_override

        # Usar workflow definido
        workflow = crew_blueprint.get('workflow', {})
        entry_point = workflow.get('entryPoint')

        if entry_point and entry_point in agents:
            return entry_point

        # Lógica simples de roteamento baseada em palavras-chave
        message_lower = message.lower()

        # Procurar por agentes especializados
        for agent_key, agent_config in agents.items():
            role = agent_config.get('role', '').lower()
            goal = agent_config.get('goal', '').lower()

            # Roteamento para vendas
            if any(word in message_lower for word in ['comprar', 'preço', 'valor', 'produto', 'venda']) and \
               any(word in role + goal for word in ['venda', 'produto', 'comercial']):
                return agent_key

            # Roteamento para suporte
            if any(word in message_lower for word in ['problema', 'erro', 'ajuda', 'suporte', 'dúvida']) and \
               any(word in role + goal for word in ['suporte', 'ajuda', 'problema', 'técnico']):
                return agent_key

        # Fallback: usar agente padrão ou primeiro ativo
        fallback_agent = workflow.get('fallbackAgent')
        if fallback_agent and fallback_agent in agents:
            return fallback_agent

        # Procurar agente geral ou de triagem
        for agent_key in agents.keys():
            if any(word in agent_key.lower() for word in ['geral', 'triagem', 'padrao']):
                return agent_key

        # Último recurso: primeiro agente ativo
        for agent_key, agent_config in agents.items():
            if agent_config.get('isActive', True):
                return agent_key

        # Se nada funcionar, usar primeiro agente
        return list(agents.keys())[0] if agents else 'geral'

    async def get_available_agents(self, tenant_id: str, crew_id: str) -> List[Dict[str, Any]]:
        """Retorna lista de agentes disponíveis na equipe"""
        try:
            if not self.db:
                # Retornar agentes demo
                return [
                    {'id': 'triagem', 'name': 'Agente de Triagem', 'role': 'Classificador', 'tools': [], 'order': 1},
                    {'id': 'vendas', 'name': 'Agente de Vendas', 'role': 'Vendedor', 'tools': ['consultar_base_conhecimento'], 'order': 2},
                    {'id': 'suporte', 'name': 'Agente de Suporte', 'role': 'Suporte', 'tools': ['consultar_base_conhecimento'], 'order': 3},
                    {'id': 'geral', 'name': 'Agente Geral', 'role': 'Atendente', 'tools': [], 'order': 4}
                ]

            crew_blueprint = await self.load_crew_blueprint(tenant_id, crew_id)
            agents = crew_blueprint.get('agents', {})

            agent_list = []
            for agent_key, agent_config in agents.items():
                if agent_config.get('isActive', True):
                    agent_list.append({
                        'id': agent_key,
                        'name': agent_config.get('name', agent_key),
                        'role': agent_config.get('role', ''),
                        'goal': agent_config.get('goal', ''),
                        'tools': agent_config.get('tools', []),
                        'order': agent_config.get('order', 999)
                    })

            # Ordenar por ordem definida
            agent_list.sort(key=lambda x: x['order'])

            return agent_list

        except Exception as e:
            print(f"Erro ao obter agentes: {e}")
            return []

    async def validate_crew_config(self, crew_blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """Valida se a configuração da equipe é válida para CrewAI"""

        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "agent_count": 0,
            "tools_count": 0
        }

        agents = crew_blueprint.get('agents', {})

        if not agents:
            validation["errors"].append("Nenhum agente definido na equipe")
            validation["valid"] = False
            return validation

        validation["agent_count"] = len(agents)

        # Validar cada agente
        for agent_key, agent_config in agents.items():
            # Campos obrigatórios
            required_fields = ['role', 'goal']
            for field in required_fields:
                if not agent_config.get(field):
                    validation["errors"].append(f"Agente '{agent_key}' está sem o campo obrigatório '{field}'")

            # Contar ferramentas
            tools = agent_config.get('tools', [])
            validation["tools_count"] += len(tools)

            # Validar ferramentas suportadas
            supported_tools = ['consultar_base_conhecimento']
            for tool in tools:
                if tool not in supported_tools:
                    validation["warnings"].append(f"Ferramenta '{tool}' do agente '{agent_key}' pode não estar implementada")

        # Validar workflow
        workflow = crew_blueprint.get('workflow', {})
        entry_point = workflow.get('entryPoint')

        if entry_point and entry_point not in agents:
            validation["errors"].append("Agente de entrada definido no workflow não existe")

        fallback_agent = workflow.get('fallbackAgent')
        if fallback_agent and fallback_agent not in agents:
            validation["warnings"].append("Agente padrão definido no workflow não existe")

        validation["valid"] = len(validation["errors"]) == 0

        return validation

# Instância global da engine
crew_engine = CrewEngine()