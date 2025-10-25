"""
Motor CrewAI Real - Implementação com framework crewai
Mantém toda a lógica de guardrails, knowledge base, tools do SimpleEngine
mas usa Agent/Task/Crew real do framework para tool calling automático
"""

import os
import json
import time
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from firebase_admin import firestore
from typing import Dict, Any, List, Optional
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool

# Importar implementações de ferramentas
from .tools import (
    create_knowledge_tool,
    _cadastrar_cliente_planilha_impl,
    _coletar_info_agendamento_impl,
    _buscar_cliente_planilha_impl,
    _enviar_imagem_impl,
    _schedule_appointment_impl
)


class RealCrewEngine:
    """Engine usando framework CrewAI real com tool calling automático"""

    def __init__(self):
        """Inicializa o motor com CrewAI real"""
        print("🚀 Inicializando RealCrewEngine com framework CrewAI...")

        try:
            self.db = firestore.client()
            print("✅ Firestore conectado")
        except Exception as e:
            print(f"❌ Erro ao conectar Firestore: {e}")
            self.db = None

        # Configurar LLM para usar Vertex AI (Gemini) ao invés de OpenAI
        # CrewAI suporta vertex_ai via modelo vertex_ai/gemini-...
        # Usar gemini-2.5-flash-lite (mesmo modelo do SimpleEngine que funciona)
        model_name = os.getenv("VERTEX_MODEL", "gemini-2.5-flash-lite")

        # Formato para CrewAI usar Vertex AI: vertex_ai/model-name
        self.llm = LLM(
            model=f"vertex_ai/{model_name}",
            temperature=0.2,  # Baixa temperatura para precisão
            max_tokens=2048
        )
        print(f"✅ LLM configurado: vertex_ai/{model_name} (temp=0.2)")

        # Keyword search tool (não usa embeddings)
        self.knowledge_tool = self._create_keyword_search_tool()
        print("✅ Knowledge search tool criado")

    def _create_keyword_search_tool(self):
        """Cria ferramenta de busca por palavra-chave na base de conhecimento"""
        class KeywordSearchTool:
            def __init__(self, db):
                self.db = db

            def _run(self, query: str, crew_id: str, max_results: int = 3, document_ids: List[str] = None, forbidden_keywords: List[str] = None) -> str:
                """Busca por palavra-chave nos vetores com filtro de guardrails"""
                try:
                    results = []
                    vectors_ref = self.db.collection('vectors').where('crewId', '==', crew_id)

                    query_lower = query.lower()
                    query_words = set(query_lower.split())

                    print(f"🔍 Buscando conhecimento: '{query}' (crew: {crew_id})")
                    if forbidden_keywords:
                        print(f"   🔒 Filtrando palavras proibidas: {forbidden_keywords}")

                    total_docs = 0
                    forbidden_filtered = 0

                    for doc in vectors_ref.stream():
                        data = doc.to_dict()
                        total_docs += 1

                        # Filtrar por documentos específicos
                        if document_ids and data.get('documentId') not in document_ids:
                            continue

                        content = data.get('content', '').lower()

                        # PRÉ-FILTRO: Verificar palavras proibidas (guardrails)
                        is_forbidden = False
                        if forbidden_keywords:
                            for keyword in forbidden_keywords:
                                if keyword in content:
                                    is_forbidden = True
                                    forbidden_filtered += 1
                                    break

                        if is_forbidden:
                            continue

                        # Calcular score baseado em palavras encontradas
                        score = 0
                        for word in query_words:
                            if word in content:
                                score += content.count(word)

                        if score > 0:
                            results.append({
                                'content': data.get('content'),
                                'metadata': data.get('metadata', {}),
                                'similarity': score
                            })

                    print(f"   📊 Total chunks: {total_docs}, Filtrados: {forbidden_filtered}, Resultados: {len(results)}")

                    # Ordenar por score
                    results.sort(key=lambda x: x['similarity'], reverse=True)

                    if not results:
                        return "Não foram encontradas informações relevantes na base de conhecimento."

                    # Formatar resultados
                    formatted = []
                    for i, r in enumerate(results[:max_results], 1):
                        source = r.get('metadata', {}).get('source', 'documento')
                        formatted.append(f"{i}. [{source.upper()}] {r['content']}")

                    return "\n".join(formatted)

                except Exception as e:
                    print(f"❌ Erro ao buscar conhecimento: {e}")
                    return "Erro ao consultar base de conhecimento."

        return KeywordSearchTool(self.db) if self.db else None

    def _create_crewai_tools(self, agent_config: Dict[str, Any], tenant_id: str, crew_id: str, contact_id: int = None, agent_document_ids: List[str] = None) -> List:
        """Cria ferramentas do CrewAI (@tool decorated functions)"""
        tools = []
        agent_tools = agent_config.get('tools', [])
        tool_configs = agent_config.get('toolConfigs', {})

        print(f"🔧 Criando ferramentas CrewAI para agente: {agent_tools}")

        # 1. CONSULTAR BASE DE CONHECIMENTO
        if 'consultar_base_conhecimento' in agent_tools and self.knowledge_tool:
            # Extrair palavras proibidas dos guardrails
            agent_training = agent_config.get('training', {})
            guardrails = agent_training.get('guardrails', {})
            dont_rules = guardrails.get('dont', [])

            forbidden_keywords = []
            for rule in dont_rules:
                rule_lower = rule.lower()
                if 'compra' in rule_lower or 'comprar' in rule_lower:
                    forbidden_keywords.extend(['compra', 'comprar', 'venda'])
                if 'vend' in rule_lower:
                    forbidden_keywords.extend(['venda', 'vender'])

            # Criar tool com closure capturando variáveis
            knowledge_tool_instance = self.knowledge_tool
            _crew_id = crew_id
            _agent_document_ids = agent_document_ids
            _forbidden_keywords = forbidden_keywords

            @tool("consultar_base_conhecimento")
            def consultar_base_conhecimento(consulta: str, max_results: int = 3) -> str:
                """
                Busca informações na base de conhecimento da empresa.
                Use quando precisar de informações sobre produtos, serviços ou procedimentos.

                Args:
                    consulta: Texto da consulta para buscar
                    max_results: Número máximo de resultados (padrão: 3)

                Returns:
                    Informações relevantes encontradas na base de conhecimento
                """
                return knowledge_tool_instance._run(
                    query=consulta,
                    crew_id=_crew_id,
                    max_results=max_results,
                    document_ids=_agent_document_ids if _agent_document_ids else None,
                    forbidden_keywords=_forbidden_keywords if _forbidden_keywords else None
                )

            tools.append(consultar_base_conhecimento)
            print("   ✅ consultar_base_conhecimento adicionada")

        # 2. SCHEDULE_APPOINTMENT (AGENDAMENTO)
        if 'schedule_appointment' in agent_tools:
            _tenant_id = tenant_id
            _contact_id = contact_id

            @tool("schedule_appointment")
            def schedule_appointment(
                date_time: str,
                body: str,
                status: str = "pending_confirmation"
            ) -> str:
                """
                Agenda um compromisso para o cliente.
                Use status='scheduled' se cliente confirmou explicitamente.
                Use status='pending_confirmation' se cliente apenas sugeriu horário.

                Args:
                    date_time: Data e hora no formato ISO 8601 (ex: '2025-10-27T08:00:00')
                    body: Descrição do agendamento (ex: 'Consulta de Cardiologia')
                    status: 'scheduled' (confirmado) ou 'pending_confirmation' (pendente)

                Returns:
                    Mensagem de sucesso ou erro do agendamento
                """
                print(f"\n📅 EXECUTANDO schedule_appointment!")
                print(f"   tenant_id: {_tenant_id}")
                print(f"   contact_id: {_contact_id}")
                print(f"   date_time: {date_time}")
                print(f"   body: {body}")
                print(f"   status: {status}")

                result = _schedule_appointment_impl(
                    tenant_id=_tenant_id,
                    contact_id=_contact_id or 0,
                    user_id=None,  # Deixar null - será atribuído manualmente depois
                    date_time=date_time,
                    body=body,
                    status=status
                )

                print(f"   Resultado: {result}")
                return result

            tools.append(schedule_appointment)
            print("   ✅ schedule_appointment adicionada")

        # 3. CADASTRAR CLIENTE EM PLANILHA (se configurado)
        if 'cadastrar_cliente_planilha' in agent_tools and 'googleSheets' in tool_configs:
            sheets_config = tool_configs['googleSheets']
            _spreadsheet_id = sheets_config.get('spreadsheetId', '')
            _range_name = sheets_config.get('rangeName', 'Clientes!A:E')
            _tenant_id = tenant_id

            if _spreadsheet_id:
                @tool("cadastrar_cliente")
                def cadastrar_cliente(nome: str, telefone: str = "", email: str = "", observacoes: str = "") -> str:
                    """
                    Cadastra um novo cliente na planilha Google Sheets.

                    Args:
                        nome: Nome completo do cliente
                        telefone: Telefone do cliente (opcional)
                        email: Email do cliente (opcional)
                        observacoes: Observações adicionais (opcional)

                    Returns:
                        Mensagem de sucesso ou erro do cadastro
                    """
                    return _cadastrar_cliente_planilha_impl(
                        spreadsheet_id=_spreadsheet_id,
                        range_name=_range_name,
                        nome=nome,
                        telefone=telefone,
                        email=email,
                        observacoes=observacoes,
                        tenant_id=_tenant_id
                    )

                tools.append(cadastrar_cliente)
                print("   ✅ cadastrar_cliente adicionada")

        print(f"✅ Total de {len(tools)} ferramentas criadas")
        return tools

    async def process_message(
        self,
        tenant_id: str,
        crew_id: str,
        message: str,
        conversation_history: List[Dict[str, Any]] = None,
        agent_override: str = None,
        remote_jid: str = None,
        contact_id: int = None,
        ticket_id: int = None
    ) -> Dict[str, Any]:
        """Processa mensagem usando CrewAI framework real"""

        start_time = time.time()
        tools_used = []

        try:
            # Se não tem DB, retorna demo
            if not self.db:
                return self._create_demo_response(message, crew_id)

            # Carregar dados da equipe
            crew_data = await self._load_crew_data(crew_id)
            if not crew_data:
                return self._create_demo_response(message, crew_id)

            # Selecionar agente (usa mesma lógica do SimpleEngine)
            selected_agent = self._select_agent(crew_data, message, agent_override)
            print(f"✅ Agente selecionado: {selected_agent.get('name')} (key: {selected_agent.get('key')})")

            # Verificar documentos específicos do agente
            agent_document_ids = selected_agent.get('knowledgeDocuments', [])

            # Criar ferramentas do CrewAI
            crewai_tools = self._create_crewai_tools(
                agent_config=selected_agent,
                tenant_id=tenant_id,
                crew_id=crew_id,
                contact_id=contact_id,
                agent_document_ids=agent_document_ids if agent_document_ids else None
            )

            # Construir contexto (guardrails, persona, examples)
            context = self._build_context(conversation_history, crew_data, selected_agent)

            # Criar agente CrewAI
            agent_role = selected_agent.get('role', 'Atendente')
            agent_goal = selected_agent.get('goal', 'Ajudar o cliente')

            crew_agent = Agent(
                role=agent_role,
                goal=agent_goal,
                backstory=context,  # Todo o contexto vai aqui
                tools=crewai_tools,
                llm=self.llm,  # Usar Vertex AI (Gemini)
                verbose=True,
                allow_delegation=False
            )

            # Criar task para processar a mensagem
            task_description = f"""
            Você recebeu a seguinte mensagem de um cliente: "{message}"

            {"Histórico da conversa:\n" + self._format_conversation_history(conversation_history) if conversation_history else ""}

            Sua tarefa é:
            1. Analisar a mensagem do cliente
            2. Usar suas ferramentas se necessário para obter informações ou executar ações
            3. Fornecer uma resposta útil, clara e personalizada
            4. Manter o tom e personalidade definidos no seu perfil
            5. SEGUIR RIGOROSAMENTE as regras de guardrails definidas

            Responda diretamente ao cliente de forma natural e conversacional.
            """

            task = Task(
                description=task_description,
                expected_output="Uma resposta clara, útil e personalizada para o cliente",
                agent=crew_agent
            )

            # Criar e executar Crew
            crew = Crew(
                agents=[crew_agent],
                tasks=[task],
                verbose=True
            )

            print("🚀 Executando CrewAI Crew...")
            print(f"   Agente: {crew_agent.role}")
            print(f"   Ferramentas disponíveis: {[str(t.name) if hasattr(t, 'name') else str(t) for t in crewai_tools]}")
            print(f"   Mensagem: {message}")

            result = crew.kickoff()

            print(f"✅ CrewAI executado com sucesso!")
            print(f"   Tipo do resultado: {type(result)}")
            print(f"   Resultado bruto: {result}")

            # Processar resultado
            response_text = str(result).strip() if result else "Desculpe, não consegui processar sua solicitação."

            # Detectar quais ferramentas foram usadas (baseado no output do CrewAI)
            result_str = str(result).lower()
            if "consultar_base_conhecimento" in result_str or "base de conhecimento" in result_str:
                tools_used.append("consultar_base_conhecimento")
                print("   🔧 Ferramenta detectada: consultar_base_conhecimento")

            if "schedule_appointment" in result_str or "agendamento criado" in result_str or "agendado" in result_str:
                tools_used.append("schedule_appointment")
                print("   🔧 Ferramenta detectada: schedule_appointment")

            if "cadastrar_cliente" in result_str or "cadastrado" in result_str:
                tools_used.append("cadastrar_cliente")
                print("   🔧 Ferramenta detectada: cadastrar_cliente")

            print(f"   Total de ferramentas usadas: {len(tools_used)}")

            processing_time = time.time() - start_time

            return {
                "response": response_text,
                "agent_used": selected_agent.get("key", "geral"),
                "agent_name": selected_agent.get("name", "Agente Geral"),
                "tools_used": tools_used,
                "success": True,
                "processing_time": round(processing_time, 2),
                "demo_mode": False
            }

        except Exception as e:
            print(f"❌ Erro no RealCrewEngine: {e}")
            import traceback
            traceback.print_exc()

            return {
                "response": f"Desculpe, ocorreu um erro interno: {str(e)}",
                "agent_used": "error",
                "agent_name": "Sistema",
                "tools_used": [],
                "success": False,
                "processing_time": time.time() - start_time,
                "demo_mode": True
            }

    async def _load_crew_data(self, crew_id: str) -> Optional[Dict[str, Any]]:
        """Carrega dados da equipe do Firestore"""
        try:
            # Tentar primeiro em 'crews' (nova estrutura)
            doc_ref = self.db.collection('crews').document(crew_id)
            doc = doc_ref.get()

            # Se não encontrar, tentar em 'crew_blueprints'
            if not doc.exists:
                doc_ref = self.db.collection('crew_blueprints').document(crew_id)
                doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                print(f"✅ Equipe carregada: {data.get('name', 'Sem nome')}")
                return data
            else:
                print(f"❌ Equipe {crew_id} não encontrada")
                return None

        except Exception as e:
            print(f"❌ Erro ao carregar equipe: {e}")
            return None

    def _select_agent(self, crew_data: Dict[str, Any], message: str, agent_override: str = None) -> Dict[str, Any]:
        """Seleciona o agente apropriado (mesma lógica do SimpleEngine)"""

        agents = crew_data.get('agents', {})

        if not agents:
            print("❌ Nenhum agente encontrado - usando padrão")
            return {"key": "geral", "name": "Agente Geral", "role": "Atendente", "goal": "Ajudar o cliente"}

        # Se tem override, usar
        if agent_override and agent_override in agents:
            agent_data = agents[agent_override]
            agent_data["key"] = agent_override
            return agent_data

        message_lower = message.lower()

        # Roteamento baseado em palavras-chave
        best_match = None
        best_score = 0

        for agent_key, agent_data in agents.items():
            if not agent_data.get('isActive', True):
                continue

            score = 0
            role = agent_data.get('role', '').lower()
            goal = agent_data.get('goal', '').lower()

            # Palavras-chave do agente
            keywords = agent_data.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    score += 3

            # Palavras do role/goal
            if any(word in message_lower for word in role.split() + goal.split()):
                score += 1

            if score > best_score:
                best_score = score
                best_match = agent_data
                best_match["key"] = agent_key

        # Se encontrou com score bom, usar
        if best_match and best_score >= 2:
            return best_match

        # Fallback: workflow entry point
        workflow = crew_data.get('workflow', {})
        entry_agent = workflow.get('entryPoint')
        if entry_agent and entry_agent in agents:
            agent_data = agents[entry_agent]
            agent_data["key"] = entry_agent
            return agent_data

        # Último recurso: primeiro agente ativo
        for agent_key, agent_data in agents.items():
            if agent_data.get('isActive', True):
                agent_data["key"] = agent_key
                return agent_data

        # Absolutamente último: primeiro da lista
        first_key = list(agents.keys())[0]
        first_agent = agents[first_key]
        first_agent["key"] = first_key
        return first_agent

    def _build_context(self, conversation_history: List[Dict[str, Any]], crew_data: Dict[str, Any], selected_agent: Dict[str, Any]) -> str:
        """Constrói contexto completo com guardrails, persona, examples (mesma lógica do SimpleEngine)"""

        context_parts = []

        # GUARDRAILS NO TOPO - PRIORIDADE MÁXIMA
        agent_training = selected_agent.get('training', {})
        guardrails = agent_training.get('guardrails', {})
        do_rules = guardrails.get('do', [])
        dont_rules = guardrails.get('dont', [])

        if do_rules or dont_rules:
            context_parts.append("⚠️⚠️⚠️ ATENÇÃO CRÍTICA - LEIA ISTO PRIMEIRO ⚠️⚠️⚠️")
            context_parts.append("="*70)
            context_parts.append("REGRAS CRÍTICAS (SIGA RIGOROSAMENTE):")
            context_parts.append("="*70)

            if dont_rules:
                context_parts.append("\n🚫 PROIBIDO - Você NÃO DEVE JAMAIS:")
                for rule in dont_rules:
                    if rule and rule.strip():
                        context_parts.append(f"  ✗ {rule}")

            if do_rules:
                context_parts.append("\n🔴 OBRIGATÓRIO - Você DEVE:")
                for rule in do_rules:
                    if rule and rule.strip():
                        context_parts.append(f"  ✓ {rule}")

            context_parts.append("\n" + "="*70)
            context_parts.append("🚨 ANTES DE RESPONDER, RELEIA AS REGRAS PROIBIDAS ACIMA 🚨")
            context_parts.append("="*70 + "\n")

        # Informações da empresa/equipe
        crew_name = crew_data.get('name', 'Equipe de Atendimento')
        crew_description = crew_data.get('description', '')

        context_parts.append(f"EMPRESA/EQUIPE: {crew_name}")
        if crew_description:
            context_parts.append(f"DESCRIÇÃO: {crew_description}")

        # Informações do agente
        agent_backstory = selected_agent.get('backstory', 'Sou um assistente especializado')
        context_parts.append(f"\nSUA HISTÓRIA: {agent_backstory}")

        # Personalidade
        personality = selected_agent.get('personality', {})
        if personality:
            tone = personality.get('tone', 'profissional')
            traits = personality.get('traits', [])
            context_parts.append(f"TOM DE VOZ: {tone}")
            if traits:
                context_parts.append(f"CARACTERÍSTICAS: {', '.join(traits)}")

            custom_instructions = personality.get('customInstructions', '').strip()
            if custom_instructions:
                context_parts.append(f"\n📋 INSTRUÇÕES PERSONALIZADAS:")
                context_parts.append(custom_instructions)

        # Persona do agente
        persona = agent_training.get('persona', '').strip()
        if persona:
            context_parts.append(f"\nSUA PERSONA:")
            context_parts.append(persona)

        # Exemplos de interação (few-shot learning)
        agent_examples = agent_training.get('examples', [])
        team_training = crew_data.get('training', {})
        team_examples = team_training.get('examples', []) if team_training else []
        all_examples = agent_examples + team_examples

        if all_examples:
            context_parts.append("\n" + "="*70)
            context_parts.append("🎯 EXEMPLOS DE RESPOSTAS CORRETAS - SIGA EXATAMENTE ESTE PADRÃO")
            context_parts.append("="*70)

            recent_examples = all_examples[-5:] if len(all_examples) > 5 else all_examples

            for i, example in enumerate(recent_examples, 1):
                scenario = example.get('scenario', '').strip()
                good = example.get('good', '').strip()
                bad = example.get('bad', '').strip()

                if scenario:
                    context_parts.append(f"\n📝 EXEMPLO {i}:")
                    context_parts.append(f"Cenário: {scenario}")
                    if good:
                        context_parts.append(f"✓ RESPOSTA CORRETA: {good}")
                    if bad:
                        context_parts.append(f"✗ RESPOSTA INCORRETA (NUNCA USE): {bad}")

            context_parts.append("\n" + "="*70)

        return "\n".join(context_parts)

    def _format_conversation_history(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Formata histórico de conversa"""
        if not conversation_history:
            return ""

        formatted = []
        for msg in conversation_history[-5:]:  # Últimas 5 mensagens
            role = "Cliente" if msg.get('role') == 'user' else "Assistente"
            content = msg.get('content', '')
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def _create_demo_response(self, message: str, crew_id: str) -> Dict[str, Any]:
        """Resposta demo sem Firestore"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['olá', 'oi', 'bom dia']):
            response = "Olá! Como posso ajudá-lo hoje?"
            agent_used = "triagem"
        elif any(word in message_lower for word in ['agendar', 'marcar', 'consulta']):
            response = "Entendo que você deseja agendar. Pode me informar o dia e horário de sua preferência?"
            agent_used = "agendamento"
        else:
            response = f"Obrigado por sua mensagem. Como posso ajudá-lo?"
            agent_used = "geral"

        return {
            "response": response,
            "agent_used": agent_used,
            "agent_name": f"Agente {agent_used.title()}",
            "tools_used": [],
            "success": True,
            "demo_mode": True
        }

    async def get_available_agents(self, tenant_id: str, crew_id: str) -> List[Dict[str, Any]]:
        """Retorna lista de agentes disponíveis"""
        try:
            crew_data = await self._load_crew_data(crew_id)
            if not crew_data:
                return []

            agents = crew_data.get('agents', {})
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

            agent_list.sort(key=lambda x: x['order'])
            return agent_list

        except Exception as e:
            print(f"❌ Erro ao obter agentes: {e}")
            return []

    async def validate_crew_config(self, crew_blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """Valida configuração da equipe"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "agent_count": 0,
            "tools_count": 0
        }

        agents = crew_blueprint.get('agents', {})

        if not agents:
            validation["errors"].append("Nenhum agente definido")
            validation["valid"] = False
            return validation

        validation["agent_count"] = len(agents)

        # Validar cada agente
        for agent_key, agent_config in agents.items():
            required_fields = ['role', 'goal']
            for field in required_fields:
                if not agent_config.get(field):
                    validation["errors"].append(f"Agente '{agent_key}' sem campo '{field}'")

            tools = agent_config.get('tools', [])
            validation["tools_count"] += len(tools)

        validation["valid"] = len(validation["errors"]) == 0
        return validation
