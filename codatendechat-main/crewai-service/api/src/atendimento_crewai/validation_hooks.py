"""
Sistema de Validação Programática 100% Genérico e Multi-Tenant

Este módulo implementa validações dinâmicas baseadas em:
1. Extração de entidades da base de conhecimento (KB) do tenant
2. Validação de consistência entre entidades extraídas da mensagem do usuário
3. Geração de mensagens de correção genéricas

NÃO CONTÉM NENHUMA LÓGICA ESPECÍFICA DE NEGÓCIO.
Toda configuração vem de Firestore (agents[].validation_config).
"""

import re
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class GenericValidationHooks:
    """
    Sistema de validação 100% genérico e multi-tenant.

    Funcionalidade:
    - Extrai vocabulário de entidades DINAMICAMENTE da KB do tenant
    - Detecta entidades na mensagem do usuário usando regex/keywords configurados
    - Valida se combinação de entidades é consistente com a KB
    - Retorna mensagens de correção genéricas

    Exemplo de uso:

    # Configuração no Firestore (agents[].validation_config):
    {
        "enabled": true,
        "rules": [
            {
                "id": "rule_123",
                "name": "Validar agendamentos",
                "trigger_keywords": ["agendar", "marcar", "consulta"],
                "entity_extraction": {
                    "service_type": {
                        "method": "regex",
                        "pattern": "consulta\\s+(?:de\\s+)?(\\w+)",
                        "description": "Tipo de consulta"
                    },
                    "time_period": {
                        "method": "keywords",
                        "pattern": "segunda,terça,quarta,quinta,sexta,sábado,domingo",
                        "description": "Dia da semana"
                    }
                },
                "strictness": "high",
                "auto_correct": false
            }
        ]
    }

    # Código Python (GENÉRICO):
    validator = GenericValidationHooks(kb_search_function)
    result = await validator.run_validation(
        message="quero marcar consulta cardiologia quarta",
        crew_id="company_1",
        doc_ids=["doc1", "doc2"],
        rule_config={...}  # From Firestore
    )

    # Resultado se houver conflito:
    {
        "valid": false,
        "conflict": {
            "detected_entities": {
                "service_type": "cardiologia",
                "time_period": "quarta"
            },
            "correction_message": "⚠️ Cardiologia não está disponível às quartas-feiras. Segundo a base de conhecimento, Cardiologia atende apenas às segundas-feiras.",
            "kb_evidence": "Cardiologista atende apenas às segundas-feiras de 8h às 12h."
        }
    }
    """

    def __init__(self, kb_search_func: Callable):
        """
        Args:
            kb_search_func: Função async para buscar na KB.
                Assinatura: async def(query: str, crew_id: str, doc_ids: List[str]) -> List[Dict]
                Retorna: [{"content": "...", "score": 0.9}, ...]
        """
        self.kb_search = kb_search_func

    async def build_entity_vocabulary_from_kb(
        self,
        crew_id: str,
        doc_ids: List[str],
        entity_types_config: Dict[str, Dict[str, str]]
    ) -> Dict[str, List[str]]:
        """
        Constrói vocabulário de entidades DINAMICAMENTE da base de conhecimento.

        Args:
            crew_id: ID do tenant (ex: "company_1")
            doc_ids: IDs dos documentos da KB a consultar
            entity_types_config: Configuração de extração por tipo de entidade
                Exemplo:
                {
                    "service_type": {
                        "method": "regex",
                        "pattern": "consulta\\s+(?:de\\s+)?(\\w+)",
                        "description": "Tipo de consulta"
                    },
                    "time_period": {
                        "method": "keywords",
                        "pattern": "segunda,terça,quarta",
                        "description": "Dia da semana"
                    },
                    "professional": {
                        "method": "line_starts",
                        "pattern": "Profissional:",
                        "description": "Nome do profissional"
                    }
                }

        Returns:
            Dicionário com vocabulário extraído por tipo de entidade
            Exemplo:
            {
                "service_type": ["cardiologia", "dermatologia", "ortopedia"],
                "time_period": ["segunda", "terça", "quarta"],
                "professional": ["Dr. João", "Dra. Maria"]
            }
        """
        logger.info(f"🔍 Construindo vocabulário de entidades da KB (crew_id={crew_id})")

        # Buscar TODO conteúdo da KB (query vazia retorna tudo)
        kb_results = await self.kb_search(query="", crew_id=crew_id, doc_ids=doc_ids)

        if not kb_results:
            logger.warning(f"⚠️ KB vazia para crew_id={crew_id}")
            return {}

        # Concatenar todo conteúdo da KB
        full_content = "\n".join([r.get('content', '') for r in kb_results])
        logger.info(f"📄 KB carregada: {len(full_content)} caracteres")

        vocabulary = {}

        for entity_type, config in entity_types_config.items():
            method = config.get('method', 'keywords')
            pattern = config.get('pattern', '')

            extracted_values = []

            if method == 'regex':
                # Extração por regex
                try:
                    matches = re.findall(pattern, full_content, re.IGNORECASE | re.MULTILINE)
                    extracted_values = list(set([m.lower().strip() for m in matches if m.strip()]))
                    logger.info(f"  📌 {entity_type} (regex): {len(extracted_values)} valores encontrados")
                except Exception as e:
                    logger.error(f"  ❌ Erro ao aplicar regex para {entity_type}: {e}")

            elif method == 'keywords':
                # Extração por lista de keywords (separadas por vírgula)
                keywords = [k.strip().lower() for k in pattern.split(',') if k.strip()]
                # Verifica quais keywords aparecem na KB
                for keyword in keywords:
                    if keyword in full_content.lower():
                        extracted_values.append(keyword)
                logger.info(f"  📌 {entity_type} (keywords): {len(extracted_values)}/{len(keywords)} encontrados")

            elif method == 'line_starts':
                # Extrai valores de linhas que começam com um prefixo específico
                # Exemplo: "Profissional: Dr. João" -> extrai "Dr. João"
                try:
                    lines = full_content.split('\n')
                    for line in lines:
                        if line.strip().startswith(pattern):
                            value = line.replace(pattern, '').strip()
                            if value:
                                extracted_values.append(value.lower())
                    extracted_values = list(set(extracted_values))
                    logger.info(f"  📌 {entity_type} (line_starts): {len(extracted_values)} valores encontrados")
                except Exception as e:
                    logger.error(f"  ❌ Erro ao extrair line_starts para {entity_type}: {e}")

            vocabulary[entity_type] = extracted_values

        logger.info(f"✅ Vocabulário construído: {sum(len(v) for v in vocabulary.values())} entidades totais")
        return vocabulary

    def extract_entities_from_message(
        self,
        message: str,
        entity_types_config: Dict[str, Dict[str, str]]
    ) -> Dict[str, Optional[str]]:
        """
        Extrai entidades da mensagem do usuário usando os mesmos padrões.

        Args:
            message: Mensagem do usuário
            entity_types_config: Mesma config usada em build_entity_vocabulary_from_kb

        Returns:
            Dicionário com entidades detectadas
            Exemplo: {"service_type": "cardiologia", "time_period": "quarta"}
        """
        logger.info(f"🔍 Extraindo entidades da mensagem: '{message}'")

        detected_entities = {}
        message_lower = message.lower()

        for entity_type, config in entity_types_config.items():
            method = config.get('method', 'keywords')
            pattern = config.get('pattern', '')

            detected_value = None

            if method == 'regex':
                try:
                    match = re.search(pattern, message_lower, re.IGNORECASE)
                    if match:
                        detected_value = match.group(1).strip() if match.groups() else match.group(0).strip()
                except Exception as e:
                    logger.error(f"  ❌ Erro ao aplicar regex para {entity_type}: {e}")

            elif method == 'keywords':
                keywords = [k.strip().lower() for k in pattern.split(',') if k.strip()]
                for keyword in keywords:
                    if keyword in message_lower:
                        detected_value = keyword
                        break  # Primeira keyword encontrada

            elif method == 'line_starts':
                # Não aplicável para mensagens curtas, pular
                pass

            if detected_value:
                detected_entities[entity_type] = detected_value
                logger.info(f"  ✅ {entity_type}: '{detected_value}'")

        logger.info(f"✅ Entidades detectadas: {len(detected_entities)}")
        return detected_entities

    async def validate_entity_consistency(
        self,
        entities: Dict[str, str],
        crew_id: str,
        doc_ids: List[str],
        strictness: str = "medium"
    ) -> Optional[Dict[str, Any]]:
        """
        Valida se combinação de entidades é CONSISTENTE com a KB.

        Args:
            entities: Entidades detectadas {"service_type": "cardiologia", "time_period": "quarta"}
            crew_id: ID do tenant
            doc_ids: IDs dos documentos da KB
            strictness: "low" | "medium" | "high" (quão rigorosa é a validação)

        Returns:
            None se válido, Dict com informações do conflito se inválido

            Exemplo de retorno (conflito detectado):
            {
                "detected_entities": {"service_type": "cardiologia", "time_period": "quarta"},
                "correction_message": "⚠️ Cardiologia não está disponível às quartas-feiras...",
                "kb_evidence": "Cardiologista atende apenas às segundas-feiras de 8h às 12h.",
                "confidence": 0.92
            }
        """
        if not entities:
            return None

        logger.info(f"🔍 Validando consistência de entidades: {entities}")

        # Construir query combinando todas as entidades
        query = " ".join(entities.values())

        # Buscar na KB com as entidades combinadas
        kb_results = await self.kb_search(query=query, crew_id=crew_id, doc_ids=doc_ids)

        if not kb_results:
            logger.warning(f"⚠️ KB não retornou resultados para query: '{query}'")
            return None

        # Pegar os top 3 resultados mais relevantes
        top_results = kb_results[:3]
        combined_kb_content = "\n".join([r.get('content', '') for r in top_results])

        logger.info(f"📄 KB retornou {len(kb_results)} resultados, analisando top 3")

        # VALIDAÇÃO: Verificar se TODAS as entidades aparecem JUNTAS no contexto da KB
        all_entities_found_together = True

        for entity_type, entity_value in entities.items():
            if entity_value.lower() not in combined_kb_content.lower():
                all_entities_found_together = False
                logger.warning(f"  ⚠️ '{entity_value}' ({entity_type}) NÃO encontrado no contexto da KB")
                break

        if all_entities_found_together:
            # VÁLIDO: Todas entidades aparecem juntas na KB
            logger.info(f"✅ Validação OK: Todas entidades consistentes com KB")
            return None

        # CONFLITO DETECTADO: Entidades não aparecem juntas
        logger.warning(f"❌ CONFLITO: Entidades inconsistentes com KB")

        # Extrair evidência da KB e gerar mensagem de correção
        conflict_info = await self._generate_correction_message(
            entities=entities,
            kb_content=combined_kb_content,
            crew_id=crew_id,
            doc_ids=doc_ids
        )

        return conflict_info

    async def _generate_correction_message(
        self,
        entities: Dict[str, str],
        kb_content: str,
        crew_id: str,
        doc_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Gera mensagem de correção genérica baseada no conflito detectado.

        Args:
            entities: Entidades detectadas que estão em conflito
            kb_content: Conteúdo relevante da KB
            crew_id: ID do tenant
            doc_ids: IDs dos documentos

        Returns:
            Dict com informações do conflito e mensagem de correção
        """
        # Tentar encontrar a informação CORRETA na KB
        # Buscar por cada entidade individualmente para encontrar o contexto correto

        correction_parts = []
        kb_evidence = kb_content[:500]  # Primeiros 500 chars como evidência

        # Para cada entidade, buscar qual é a informação correta
        for entity_type, entity_value in entities.items():
            # Buscar só por essa entidade
            entity_results = await self.kb_search(query=entity_value, crew_id=crew_id, doc_ids=doc_ids)

            if entity_results:
                # Pegar primeira sentença relevante
                first_result = entity_results[0].get('content', '')
                sentences = first_result.split('.')
                relevant_sentence = sentences[0] if sentences else first_result

                # Adicionar à mensagem de correção
                correction_parts.append(f"{relevant_sentence.strip()}")

        # Construir mensagem genérica
        entity_names = ", ".join([f"'{v}'" for v in entities.values()])

        correction_message = f"⚠️ A combinação {entity_names} pode não estar disponível.\n\n"
        correction_message += "Segundo a base de conhecimento:\n"
        correction_message += "\n".join([f"• {part}" for part in correction_parts if part])
        correction_message += "\n\nPor favor, verifique a disponibilidade correta."

        return {
            "detected_entities": entities,
            "correction_message": correction_message,
            "kb_evidence": kb_evidence,
            "confidence": 0.85  # Confiança genérica (pode ser ajustada)
        }

    async def run_validation(
        self,
        message: str,
        crew_id: str,
        doc_ids: List[str],
        rule_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Executa validação completa: extração + validação + correção.

        Args:
            message: Mensagem do usuário
            crew_id: ID do tenant
            doc_ids: IDs dos documentos da KB
            rule_config: Configuração da regra do Firestore
                {
                    "id": "rule_123",
                    "trigger_keywords": ["agendar", "marcar"],
                    "entity_extraction": {...},
                    "strictness": "high",
                    "auto_correct": false
                }

        Returns:
            None se validação passou, Dict com conflito se falhou
            {
                "valid": false,
                "conflict": {
                    "detected_entities": {...},
                    "correction_message": "...",
                    "kb_evidence": "...",
                    "confidence": 0.85
                }
            }
        """
        # 1. Verificar se mensagem contém trigger keywords
        trigger_keywords = rule_config.get('trigger_keywords', [])
        message_lower = message.lower()

        triggered = any(keyword.lower() in message_lower for keyword in trigger_keywords)

        if not triggered:
            logger.info(f"⏭️ Regra '{rule_config.get('name')}' não disparada (sem trigger keywords)")
            return None

        logger.info(f"🎯 Regra '{rule_config.get('name')}' DISPARADA")

        # 2. Extrair entidades da mensagem
        entity_extraction_config = rule_config.get('entity_extraction', {})
        detected_entities = self.extract_entities_from_message(
            message=message,
            entity_types_config=entity_extraction_config
        )

        if not detected_entities:
            logger.info(f"⏭️ Nenhuma entidade detectada, validação pulada")
            return None

        # 3. Validar consistência com KB
        strictness = rule_config.get('strictness', 'medium')
        conflict = await self.validate_entity_consistency(
            entities=detected_entities,
            crew_id=crew_id,
            doc_ids=doc_ids,
            strictness=strictness
        )

        if conflict:
            logger.warning(f"❌ CONFLITO DETECTADO: {conflict['correction_message'][:100]}...")
            return {
                "valid": False,
                "conflict": conflict,
                "rule_id": rule_config.get('id'),
                "rule_name": rule_config.get('name')
            }

        logger.info(f"✅ Validação OK")
        return None


# ============================================================================
# FUNÇÕES AUXILIARES PARA TESTING/DEBUG
# ============================================================================

async def test_validation_hooks():
    """
    Função de teste para validar o sistema de hooks sem depender do resto da infra.
    """
    # Mock da função de busca na KB
    async def mock_kb_search(query: str, crew_id: str, doc_ids: List[str]) -> List[Dict]:
        # Simular base de conhecimento de uma clínica médica
        mock_kb = [
            {
                "content": "Cardiologista atende apenas às segundas-feiras de 8h às 12h. Consulta de cardiologia.",
                "score": 0.95
            },
            {
                "content": "Dermatologista atende às terças e quintas-feiras de 14h às 18h. Consulta de dermatologia.",
                "score": 0.90
            },
            {
                "content": "Ortopedista atende às quartas-feiras de 9h às 13h. Consulta de ortopedia.",
                "score": 0.88
            }
        ]

        if not query:
            return mock_kb

        # Filtrar por relevância simulada
        query_lower = query.lower()
        return [doc for doc in mock_kb if query_lower in doc['content'].lower()]

    # Configuração de teste
    rule_config = {
        "id": "test_rule_1",
        "name": "Validar agendamentos médicos",
        "trigger_keywords": ["agendar", "marcar", "consulta"],
        "entity_extraction": {
            "service_type": {
                "method": "regex",
                "pattern": r"consulta\s+(?:de\s+)?(\w+)",
                "description": "Tipo de consulta"
            },
            "time_period": {
                "method": "keywords",
                "pattern": "segunda,terça,quarta,quinta,sexta,sábado,domingo",
                "description": "Dia da semana"
            }
        },
        "strictness": "high",
        "auto_correct": False
    }

    # Criar instância
    validator = GenericValidationHooks(kb_search_func=mock_kb_search)

    # Teste 1: Mensagem VÁLIDA
    print("\n" + "="*80)
    print("TESTE 1: Mensagem VÁLIDA (cardiologia na segunda)")
    print("="*80)
    result1 = await validator.run_validation(
        message="quero marcar consulta cardiologia segunda",
        crew_id="test_company",
        doc_ids=["doc1"],
        rule_config=rule_config
    )
    print(f"Resultado: {result1}")

    # Teste 2: Mensagem INVÁLIDA (conflito)
    print("\n" + "="*80)
    print("TESTE 2: Mensagem INVÁLIDA (cardiologia na quarta - CONFLITO)")
    print("="*80)
    result2 = await validator.run_validation(
        message="quero marcar consulta cardiologia quarta",
        crew_id="test_company",
        doc_ids=["doc1"],
        rule_config=rule_config
    )
    print(f"Resultado: {result2}")

    # Teste 3: Mensagem sem trigger keywords
    print("\n" + "="*80)
    print("TESTE 3: Mensagem sem trigger keywords")
    print("="*80)
    result3 = await validator.run_validation(
        message="bom dia, tudo bem?",
        crew_id="test_company",
        doc_ids=["doc1"],
        rule_config=rule_config
    )
    print(f"Resultado: {result3}")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_validation_hooks())
