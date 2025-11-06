# crew_engine_real.py - Motor CrewAI COMPLETO com logging no backend e Knowledge Base

from typing import Dict, Any, List, Optional
import time
import os
import requests
import unicodedata
from datetime import datetime
from crewai import Agent, Task, Crew, Process
from langchain_google_vertexai import ChatVertexAI
from simple_knowledge_service import get_knowledge_service

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

class RealCrewEngine:
    """Motor CrewAI completo com suporte a sequential, hierarchical, manager, logging e Knowledge Base"""

    def __init__(self):
        print("🚀 Inicializando RealCrewEngine...")
        self.llm = None
        self.knowledge_service = get_knowledge_service()
        self._initialize_llm()

    def _initialize_llm(self):
        """Inicializa o modelo Vertex AI padrão"""
        try:
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
            
            self.llm = ChatVertexAI(
                model="gemini-2.0-flash-lite",
                project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                location=os.getenv("GOOGLE_CLOUD_LOCATION"),
                temperature=0.7,
                max_output_tokens=1024,
            )
            print("✅ Vertex AI (gemini-2.0-flash-lite) inicializado com sucesso!")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar Vertex AI: {e}")
            self.llm = None

    def _save_log_to_backend(self, log_data: Dict[str, Any]):
        """Salva log no backend"""
        try:
            response = requests.post(
                f"{BACKEND_URL}/agent-logs",
                json=log_data,
                timeout=5
            )
            if response.status_code == 201:
                print(f"✅ Log salvo no backend (ID: {response.json().get('log', {}).get('id')})")
            else:
                print(f"⚠️ Erro ao salvar log: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Erro ao conectar com backend para salvar log: {e}")

    def _get_llm_for_team(self, team_config: Dict[str, Any]) -> ChatVertexAI:
        """Cria LLM customizado baseado nas configurações da equipe"""
        temperature = team_config.get('temperature', 0.7)
        model = "gemini-2.0-flash-lite"
        
        if team_config.get('processType') == 'hierarchical' and team_config.get('managerLLM'):
            model = team_config['managerLLM']
        
        try:
            llm = ChatVertexAI(
                model=model,
                project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                location=os.getenv("GOOGLE_CLOUD_LOCATION"),
                temperature=temperature,
                max_output_tokens=1024,
            )
            print(f"✅ LLM customizado criado: {model}, temperature={temperature}")
            return llm
        except Exception as e:
            print(f"⚠️ Erro ao criar LLM customizado: {e}, usando padrão")
            return self.llm

    def _normalize_text(self, text: str) -> str:
        """Remove acentos e normaliza texto para comparação"""
        # Normaliza para NFD (separa caracteres base de acentos)
        nfd = unicodedata.normalize('NFD', text)
        # Remove acentos (categoria 'Mn' = Nonspacing Mark)
        return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn').lower()

    def _select_agent_by_keywords(self, message: str, agents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Seleciona o agente mais apropriado baseado nas palavras-chave"""
        message_normalized = self._normalize_text(message)

        print("\n" + "="*60)
        print("🔍 MATCHING DE KEYWORDS - DEBUG DETALHADO")
        print("="*60)
        print(f"📝 Mensagem original: '{message}'")
        print(f"📝 Mensagem normalizada: '{message_normalized}'")
        print("="*60)

        agent_scores = []

        for agent in agents:
            agent_name = agent.get('name', 'Unknown')

            if not agent.get('isActive', True):
                print(f"⏭️  Agente '{agent_name}' está INATIVO, pulando...")
                continue

            score = 0
            keywords = agent.get('keywords', [])
            matched_keywords = []

            print(f"\n🤖 Testando agente: {agent_name}")
            print(f"   Keywords configuradas: {keywords}")

            if keywords:
                for keyword in keywords:
                    keyword_normalized = self._normalize_text(keyword)
                    print(f"   🔑 Keyword '{keyword}' → normalizada: '{keyword_normalized}'")

                    if keyword_normalized in message_normalized:
                        score += 1
                        matched_keywords.append(keyword)
                        print(f"      ✅ MATCH! '{keyword_normalized}' encontrado em '{message_normalized}'")
                    else:
                        print(f"      ❌ Não encontrado")
            else:
                print(f"   ⚠️  Agente sem keywords configuradas")

            if score > 0:
                agent_scores.append((agent, score))
                print(f"   📊 Score final: {score} (keywords matched: {matched_keywords})")
            else:
                print(f"   📊 Score final: 0 (nenhuma keyword matched)")

        print("\n" + "="*60)
        print("📊 RESULTADO DO MATCHING")
        print("="*60)

        if agent_scores:
            agent_scores.sort(key=lambda x: x[1], reverse=True)
            selected = agent_scores[0][0]
            print(f"✅ AGENTE SELECIONADO: {selected.get('name')} (score: {agent_scores[0][1]})")
            print(f"   Total de agentes com match: {len(agent_scores)}")
            if len(agent_scores) > 1:
                print(f"   Outros candidatos:")
                for agent, score in agent_scores[1:]:
                    print(f"      - {agent.get('name')}: score {score}")
            print("="*60 + "\n")
            return selected

        print("⚠️  NENHUMA KEYWORD MATCHED - Usando agente padrão")
        for agent in agents:
            if agent.get('isActive', True):
                print(f"✅ AGENTE PADRÃO SELECIONADO: {agent.get('name')}")
                print("="*60 + "\n")
                return agent

        print("❌ NENHUM AGENTE ATIVO ENCONTRADO")
        print("="*60 + "\n")
        return None

    def _build_full_prompt(self, message: str, agent_data: Dict[str, Any], conversation_history: List[Dict[str, Any]], knowledge_context: Optional[str] = None) -> str:
        """Constrói o prompt completo com TODAS as configurações do agente + Knowledge Base"""

        name = agent_data.get('name', 'Agente')
        role = agent_data.get('function', 'Assistente de atendimento')
        objective = agent_data.get('objective', 'Ajudar o cliente')
        backstory = agent_data.get('backstory', '')
        custom_instructions = agent_data.get('customInstructions', '')
        persona = agent_data.get('persona', '')
        do_list = agent_data.get('doList', [])
        dont_list = agent_data.get('dontList', [])

        print("\n" + "="*60)
        print("📋 CONFIGURAÇÃO DO AGENTE:")
        print("="*60)
        print(f"👤 Nome: {name}")
        print(f"💼 Função: {role}")
        print(f"🎯 Objetivo: {objective}")
        print(f"✅ DO List ({len(do_list)} itens): {do_list}")
        print(f"❌ DONT List ({len(dont_list)} itens): {dont_list}")
        if knowledge_context:
            print(f"📚 Knowledge Base: SIM ({len(knowledge_context)} chars)")
        print("="*60 + "\n")

        prompt_parts = []
        prompt_parts.append(f"Você é {name}, {role}.")
        prompt_parts.append(f"\nSeu objetivo é: {objective}")

        if backstory:
            prompt_parts.append(f"\n\n**SUA HISTÓRIA E CONTEXTO:**\n{backstory}")

        if persona:
            prompt_parts.append(f"\n\n**SUA PERSONA:**\n{persona}")

        if custom_instructions:
            prompt_parts.append(f"\n\n**INSTRUÇÕES ESPECIAIS:**\n{custom_instructions}")

        # ADICIONAR KNOWLEDGE BASE LOGO APÓS INSTRUÇÕES
        if knowledge_context:
            prompt_parts.append(f"\n\n**📚 INFORMAÇÕES DA BASE DE CONHECIMENTO:**")
            prompt_parts.append(knowledge_context)
            prompt_parts.append("\nIMPORTANTE: Quando houver informações na Base de Conhecimento relevantes à pergunta do cliente, use-as como referência principal. NÃO invente informações que não estejam na base.")

        if do_list:
            prompt_parts.append("\n\n**VOCÊ DEVE:**")
            for item in do_list:
                prompt_parts.append(f"- {item}")

        if dont_list:
            prompt_parts.append("\n\n**VOCÊ NÃO DEVE:**")
            for item in dont_list:
                prompt_parts.append(f"- {item}")

        if conversation_history:
            prompt_parts.append("\n\n**HISTÓRICO DA CONVERSA:**")
            # Agora usando últimas 10 mensagens do Firestore (não 5)
            for msg in conversation_history:
                role_label = msg.get('role', 'Cliente')
                prompt_parts.append(f"{role_label}: {msg.get('body', '')}")

        prompt_parts.append(f"\n\n**MENSAGEM ATUAL DO CLIENTE:**\n{message}")
        print("PROMPT COMPLETO:")
        full_prompt = "".join(prompt_parts)
        print(full_prompt[:2000])
        return full_prompt
        prompt_parts.append("\n\n**SUA RESPOSTA:**")
        prompt_parts.append("Responda de acordo com sua persona, instruções e objetivo.")

        return "\n".join(prompt_parts)

    def _create_simple_response(self, message: str, agent_data: Dict[str, Any], conversation_history: List[Dict[str, Any]], llm: ChatVertexAI, knowledge_context: Optional[str] = None) -> str:
        """Gera resposta usando Vertex AI diretamente"""
        try:
            prompt = self._build_full_prompt(message, agent_data, conversation_history, knowledge_context)
            
            from langchain_core.messages import HumanMessage
            response = llm.invoke([HumanMessage(content=prompt)])
            
            print("\n" + "="*60)
            print("📥 RESPOSTA RECEBIDA:")
            print("="*60)
            print(response.content)
            print("="*60 + "\n")
            
            return response.content
            
        except Exception as e:
            print(f"❌ Erro ao gerar resposta: {e}")
            import traceback
            traceback.print_exc()
            return "Olá! Como posso ajudá-lo hoje?"

    async def run_playground_crew(
        self,
        team_definition: Dict[str, Any],
        task: str,
        company_id: int
    ) -> Dict[str, Any]:
        """
        Executa uma Crew TEMPORÁRIA no modo Playground (não salva logs no banco).
        Usado para testar e refinar prompts antes de salvar alterações.
        """
        print("\n" + "="*60)
        print("🧪 RUN PLAYGROUND CREW - Executando equipe temporária")
        print("="*60)

        # Capturar logs verbosos
        import io
        import sys
        log_capture = io.StringIO()
        original_stdout = sys.stdout

        success = False
        response_text = ""
        error_message = None
        agent_used = None
        execution_logs = ""

        try:
            # Extrair dados da definição temporária
            team_name = team_definition.get('name', 'Equipe Temporária')
            agents_data = team_definition.get('agents', [])
            process_type = team_definition.get('processType', 'sequential')
            temperature = team_definition.get('temperature', 0.7)

            print(f"Team: {team_name}")
            print(f"Process Type: {process_type}")
            print(f"Temperature: {temperature}")
            print(f"Agents: {len(agents_data)}")
            print(f"Task: {task}")
            print("="*60 + "\n")

            if not agents_data:
                raise ValueError("A equipe precisa ter pelo menos 1 agente")

            if not self.llm:
                raise ValueError("LLM não inicializado")

            # Criar LLM customizado
            custom_llm = self._get_llm_for_team({
                'temperature': temperature,
                'processType': process_type,
                'managerLLM': team_definition.get('managerLLM')
            })

            # Selecionar agente por keywords
            selected_agent_data = self._select_agent_by_keywords(task, agents_data)
            if not selected_agent_data:
                # Se não houver match, usar primeiro agente ativo
                selected_agent_data = next((a for a in agents_data if a.get('isActive', True)), agents_data[0])

            agent_used = selected_agent_data.get('name', 'Agente')

            print(f"✅ Agente selecionado: {agent_used}")

            # Buscar Knowledge Base se configurado (opcional no playground)
            knowledge_context = None
            if selected_agent_data.get('useKnowledgeBase'):
                kb_ids = selected_agent_data.get('knowledgeBaseIds', [])
                if kb_ids:
                    print(f"📚 Buscando Knowledge Base...")
                    try:
                        # Usar teamId da definição se existir
                        team_id_for_kb = str(team_definition.get('id', 'playground'))
                        kb_chunks = self.knowledge_service.search_knowledge(
                            team_id=team_id_for_kb,
                            document_ids=kb_ids,
                            query=task,
                            top_k=20
                        )

                        if kb_chunks:
                            knowledge_context = "\n\n".join([
                                f"📄 {chunk['metadata'].get('filename', 'Documento')}: {chunk['content']}"
                                for chunk in kb_chunks
                            ])
                            print(f"✅ {len(kb_chunks)} chunks encontrados")
                    except Exception as e:
                        print(f"⚠️ Erro ao buscar KB (não crítico no playground): {e}")

            # Redirecionar stdout para capturar logs
            sys.stdout = log_capture

            # Gerar resposta
            start_time = time.time()
            response_text = self._create_simple_response(
                task,
                selected_agent_data,
                [],  # Sem histórico no playground
                custom_llm,
                knowledge_context
            )
            elapsed_time = time.time() - start_time

            # Restaurar stdout
            sys.stdout = original_stdout
            execution_logs = log_capture.getvalue()

            success = True

            print(f"✅ Resposta gerada em {elapsed_time:.2f}s")
            print(f"📝 Logs capturados: {len(execution_logs)} caracteres")

            return {
                "success": True,
                "final_output": response_text,
                "execution_logs": execution_logs,
                "agent_used": agent_used,
                "config_used": {
                    "process_type": process_type,
                    "temperature": temperature,
                    "agent_name": agent_used
                },
                "processing_time": round(elapsed_time, 2)
            }

        except Exception as e:
            # Restaurar stdout em caso de erro
            sys.stdout = original_stdout
            execution_logs = log_capture.getvalue()

            print(f"❌ Erro no playground: {e}")
            import traceback
            traceback.print_exc()

            error_message = str(e)

            return {
                "success": False,
                "final_output": f"Erro ao executar playground: {error_message}",
                "execution_logs": execution_logs + f"\n\nERRO: {error_message}",
                "error": error_message,
                "agent_used": agent_used,
                "processing_time": 0
            }

    async def process_message(
        self,
        tenant_id: str,
        crew_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        team_data: Optional[Dict[str, Any]] = None,
        agent_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """Processa mensagem usando configurações avançadas da equipe"""
        
        print("\n" + "="*60)
        print("🎯 PROCESSANDO MENSAGEM - CrewAI Real Engine")
        print("="*60)
        print(f"Tenant ID: {tenant_id}")
        print(f"Crew ID: {crew_id}")
        print(f"Mensagem: {message}")
        print("="*60 + "\n")

        success = False
        response_text = ""
        error_message = None
        selected_agent_data = None
        prompt_used = ""

        try:
            if not self.llm:
                error_message = "LLM não inicializado"
                return {
                    "success": False,
                    "response": "Desculpe, o serviço de IA não está disponível no momento.",
                    "error": error_message
                }

            if not team_data:
                error_message = "No team data provided"
                return {
                    "success": False,
                    "response": "Desculpe, não foi possível processar sua mensagem. Equipe não configurada.",
                    "error": error_message
                }

            agents = team_data.get('agents', [])
            if not agents:
                error_message = "No agents in team"
                return {
                    "success": False,
                    "response": "Desculpe, não há agentes disponíveis nesta equipe.",
                    "error": error_message
                }

            process_type = team_data.get('processType', 'sequential')
            temperature = team_data.get('temperature', 0.7)
            verbose = team_data.get('verbose', True)

            print(f"\n⚙️ CONFIGURAÇÕES DA EQUIPE:")
            print(f"   Process Type: {process_type}")
            print(f"   Temperature: {temperature}")
            print(f"   Verbose: {verbose}")
            print(f"   Total de agentes: {len(agents)}\n")

            custom_llm = self._get_llm_for_team({
                'temperature': temperature,
                'processType': process_type,
                'managerLLM': team_data.get('managerLLM')
            })

            selected_agent_data = self._select_agent_by_keywords(message, agents)
            if not selected_agent_data:
                error_message = "No appropriate agent found"
                return {
                    "success": False,
                    "response": "Desculpe, não consegui encontrar um agente apropriado para sua solicitação.",
                    "error": error_message
                }

            print(f"✅ Usando agente: {selected_agent_data.get('name')}")

            # Buscar Knowledge Base se o agente usar
            knowledge_context = None
            kb_chunks = []
            kb_usage_info = None

            if selected_agent_data.get('useKnowledgeBase'):
                kb_ids = selected_agent_data.get('knowledgeBaseIds', [])
                if kb_ids:
                    print(f"📚 Buscando Knowledge Base: {len(kb_ids)} documentos")
                    try:
                        kb_chunks = self.knowledge_service.search_knowledge(
                            team_id=str(crew_id),
                            document_ids=kb_ids,
                            query=message,
                            top_k=20
                        )

                        if kb_chunks:
                            knowledge_context = "\n\n".join([
                                f"📄 {chunk['metadata'].get('filename', 'Documento')}: {chunk['content']}"
                                for chunk in kb_chunks
                            ])
                            print(f"✅ {len(kb_chunks)} chunks relevantes encontrados do KB")

                            # Preparar info de KB para o log
                            kb_usage_info = {
                                "used": True,
                                "documentsSearched": len(kb_ids),
                                "chunksFound": len(kb_chunks),
                                "chunks": [
                                    {
                                        "filename": chunk['metadata'].get('filename', 'Documento'),
                                        "documentId": chunk.get('documentId'),
                                        "similarity": round(chunk.get('similarity', 0), 3),
                                        "contentPreview": chunk['content'][:100] + "..." if len(chunk['content']) > 100 else chunk['content']
                                    }
                                    for chunk in kb_chunks
                                ]
                            }
                        else:
                            print("📭 Nenhum chunk relevante encontrado")
                            kb_usage_info = {
                                "used": True,
                                "documentsSearched": len(kb_ids),
                                "chunksFound": 0,
                                "chunks": []
                            }
                    except Exception as e:
                        print(f"⚠️ Erro ao buscar KB: {e}")
                        kb_usage_info = {
                            "used": True,
                            "documentsSearched": len(kb_ids),
                            "chunksFound": 0,
                            "error": str(e)
                        }

            print("🚀 Gerando resposta com Vertex AI...")
            start_time = time.time()

            prompt_used = self._build_full_prompt(
                message,
                selected_agent_data,
                conversation_history or [],
                knowledge_context
            )
            response_text = self._create_simple_response(
                message,
                selected_agent_data,
                conversation_history or [],
                custom_llm,
                knowledge_context
            )
            
            elapsed_time = time.time() - start_time
            success = True

            print(f"✅ Resposta gerada em {elapsed_time:.2f}s")

            # Salvar log no backend
            log_data = {
                "companyId": int(tenant_id),
                "teamId": int(crew_id),
                "agentId": selected_agent_data.get('id'),
                "message": message,
                "response": response_text,
                "agentConfig": {
                    "name": selected_agent_data.get('name'),
                    "function": selected_agent_data.get('function'),
                    "objective": selected_agent_data.get('objective'),
                    "keywords": selected_agent_data.get('keywords', []),
                    "useKnowledgeBase": selected_agent_data.get('useKnowledgeBase', False)
                },
                "knowledgeBaseUsage": kb_usage_info,
                "teamConfig": {
                    "processType": process_type,
                    "temperature": temperature,
                    "verbose": verbose
                },
                "promptUsed": prompt_used,
                "processingTime": round(elapsed_time, 2),
                "success": True,
                "errorMessage": None
            }
            
            self._save_log_to_backend(log_data)

            return {
                "success": True,
                "response": response_text,
                "agent_used": selected_agent_data.get('name'),
                "processing_time": round(elapsed_time, 2),
                "config_used": {
                    "process_type": process_type,
                    "temperature": temperature,
                    "verbose": verbose
                }
            }

        except Exception as e:
            print(f"❌ Erro ao processar mensagem: {e}")
            import traceback
            traceback.print_exc()
            error_message = str(e)
            
            # Salvar log de erro
            if selected_agent_data and team_data:
                log_data = {
                    "companyId": int(tenant_id),
                    "teamId": int(crew_id),
                    "agentId": selected_agent_data.get('id'),
                    "message": message,
                    "response": "Erro ao processar",
                    "agentConfig": {"name": selected_agent_data.get('name')},
                    "teamConfig": {"processType": team_data.get('processType', 'sequential')},
                    "promptUsed": prompt_used if prompt_used else None,
                    "processingTime": 0,
                    "success": False,
                    "errorMessage": error_message
                }
                self._save_log_to_backend(log_data)
            
            return {
                "success": False,
                "response": "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
                "error": error_message
            }
