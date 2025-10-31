# Guia Completo do Sistema AtendChat

## Índice

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Arquitetura Técnica](#2-arquitetura-técnica)
3. [Componentes do Sistema](#3-componentes-do-sistema)
4. [Guia de Uso - Frontend](#4-guia-de-uso---frontend)
5. [Criação e Configuração de Crews](#5-criação-e-configuração-de-crews)
6. [Base de Conhecimento](#6-base-de-conhecimento)
7. [Agentes de IA](#7-agentes-de-ia)
8. [Guardrails (Regras de Comportamento)](#8-guardrails-regras-de-comportamento)
9. [Ferramentas Disponíveis](#9-ferramentas-disponíveis)
10. [Integração WhatsApp](#10-integração-whatsapp)
11. [Deploy e Manutenção](#11-deploy-e-manutenção)
12. [Troubleshooting](#12-troubleshooting)
13. [Boas Práticas](#13-boas-práticas)
14. [Limitações e Considerações](#14-limitações-e-considerações)

---

## 1. Visão Geral do Sistema

### 1.1 O que é o AtendChat?

O AtendChat é uma plataforma de atendimento automatizado via WhatsApp que utiliza **Inteligência Artificial (IA)** para criar equipes de agentes virtuais especializados. Cada equipe (Crew) pode ter múltiplos agentes, cada um com sua função específica, conhecimento e comportamento personalizado.

### 1.2 Casos de Uso

- **Imobiliárias**: Agentes para vendas, locação, triagem de leads
- **Restaurantes**: Atendimento, pedidos, cardápio digital
- **Clínicas**: Agendamento, triagem, informações sobre serviços
- **E-commerce**: Vendas, suporte, consulta de produtos
- **Qualquer negócio**: Atendimento personalizado 24/7

### 1.3 Principais Funcionalidades

- ✅ Múltiplos agentes especializados por equipe
- ✅ Base de conhecimento com upload de documentos (PDF, TXT, DOCX, etc.)
- ✅ Seleção automática do agente correto baseada em palavras-chave
- ✅ Guardrails (regras de comportamento) personalizáveis
- ✅ Integração nativa com WhatsApp
- ✅ Ferramentas customizáveis (Google Sheets, agendamento, etc.)
- ✅ Histórico de conversas
- ✅ Multi-tenancy (múltiplas empresas no mesmo sistema)

---

## 2. Arquitetura Técnica

### 2.1 Componentes Principais

```
┌─────────────────────────────────────────────────────────┐
│                    USUÁRIO (WhatsApp)                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              FRONTEND (React + Material-UI)              │
│  - Interface de gerenciamento de crews                   │
│  - Configuração de agentes                               │
│  - Upload de documentos                                  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│           BACKEND (Node.js + TypeScript)                 │
│  - API REST                                              │
│  - Autenticação                                          │
│  - Gerenciamento de crews                                │
│  - Proxy para CrewAI Service                             │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│         CREWAI SERVICE (Python + FastAPI)                │
│  - Motor de processamento de IA                          │
│  - Seleção de agentes                                    │
│  - Base de conhecimento (vetorização)                    │
│  - Integração com Gemini AI                              │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              FIRESTORE (Banco de Dados)                  │
│  - Crews e configurações                                 │
│  - Documentos de conhecimento                            │
│  - Vetores (chunks de documentos)                        │
│  - Histórico de conversas                                │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Stack Tecnológica

**Frontend:**
- React 17
- Material-UI
- Formik (formulários)
- Axios (requisições HTTP)

**Backend:**
- Node.js
- TypeScript
- Express
- Multer (upload de arquivos)
- Docker

**CrewAI Service:**
- Python 3.12
- FastAPI
- Google Vertex AI (Gemini)
- Firebase Admin SDK
- PyPDF2, python-docx (processamento de documentos)

**Infraestrutura:**
- Google Cloud Platform (Firestore, Vertex AI)
- Docker & Docker Compose
- Systemd (gerenciamento de serviços)

### 2.3 Fluxo de Dados

1. **Mensagem do WhatsApp chega** → Backend recebe
2. **Backend identifica a crew** → Consulta Firestore
3. **Backend envia para CrewAI Service** → Processamento IA
4. **CrewAI Service:**
   - Seleciona o agente correto (baseado em keywords)
   - Consulta base de conhecimento (se configurado)
   - Executa ferramentas (se necessário)
   - Gera resposta usando Gemini AI
5. **Resposta retorna** → Backend → WhatsApp

---

## 3. Componentes do Sistema

### 3.1 Crews (Equipes)

Uma **Crew** é uma equipe de agentes de IA que trabalham juntos para atender um determinado contexto de negócio.

**Campos:**
- `name`: Nome da equipe (ex: "Equipe Imobiliária Inteligente")
- `description`: Descrição do propósito da equipe
- `agents`: Array de agentes (mínimo 1)
- `tenantId`: ID da empresa/tenant
- `createdAt`: Data de criação

### 3.2 Agentes

Um **Agente** é um membro da equipe com função especializada.

**Campos principais:**
- `name`: Nome do agente (ex: "Ana - Especialista em Vendas")
- `role`: Papel do agente (ex: "Agente Especialista em Vendas")
- `goal`: Objetivo do agente (ex: "Apresentar opções de imóveis para venda")
- `backstory`: História/contexto do agente
- `keywords`: Palavras-chave para seleção automática
- `tools`: Ferramentas disponíveis para o agente
- `knowledgeDocuments`: IDs dos documentos da base de conhecimento
- `training.guardrails`: Regras de comportamento (do/don't)
- `personality`: Tom de voz e instruções customizadas

### 3.3 Base de Conhecimento

Sistema de armazenamento e busca de informações baseado em documentos.

**Collections no Firestore:**

1. **`knowledge_documents`**: Metadados dos documentos
   - `crewId`: ID da crew
   - `documentId`: ID único do documento
   - `filename`: Nome do arquivo
   - `fileType`: Tipo (pdf, text, word, excel)
   - `fileSize`: Tamanho em bytes
   - `chunksCount`: Número de chunks criados
   - `wordCount`: Número de palavras
   - `uploadedAt`: Data de upload
   - `status`: Status do processamento

2. **`vectors`**: Chunks vetorizados dos documentos
   - `crewId`: ID da crew (IMPORTANTE: usado para filtrar)
   - `documentId`: ID do documento original
   - `chunkId`: ID único do chunk
   - `content`: Conteúdo textual do chunk
   - `embedding`: Vetor de embeddings (se disponível)
   - `hasEmbedding`: Boolean indicando se tem embedding
   - `metadata`: Metadados adicionais
   - `chunkIndex`: Índice do chunk no documento

---

## 4. Guia de Uso - Frontend

### 4.1 Acessando o Sistema

1. Acesse a URL do frontend: `https://atendeaibr.com`
2. Faça login com suas credenciais
3. Navegue até o menu "Crews" (Equipes)

### 4.2 Interface Principal

A interface de Crews possui:
- **Lista de Crews**: Visualização de todas as equipes criadas
- **Botão "+ Nova Crew"**: Criar nova equipe
- **Ações por Crew**: Editar, Duplicar, Deletar

---

## 5. Criação e Configuração de Crews

### 5.1 Criando uma Nova Crew

1. Clique em **"+ Nova Crew"**
2. Um modal abrirá com 3 abas:
   - **Geral**: Nome e descrição da crew
   - **Agentes**: Configuração dos agentes
   - **Base de Conhecimento**: Upload de documentos

### 5.2 Aba Geral

**Nome da Crew:**
- Escolha um nome descritivo
- Exemplo: "Equipe Imobiliária WhatsApp"

**Descrição:**
- Descreva o propósito da equipe
- Exemplo: "Equipe de agentes de IA especializada em atendimento imobiliário via WhatsApp"

### 5.3 Aba Agentes

Aqui você configura cada agente da equipe.

#### 5.3.1 Campos Obrigatórios

**Nome do Agente:**
- Formato recomendado: "Nome - Especialidade"
- Exemplo: "Ana - Especialista em Vendas"

**Papel (Role):**
- Defina a função do agente
- Exemplo: "Agente Especialista em Vendas"

**Objetivo (Goal):**
- Descreva o que o agente deve fazer
- Seja específico e claro
- Exemplo: "Apresentar opções de imóveis para venda, fornecer informações sobre financiamento e auxiliar o cliente em todo o processo de compra."

**História (Backstory):**
- Contexto e experiência do agente
- Ajuda a definir a "personalidade"
- Exemplo: "Ana é uma especialista em vendas com ampla experiência no mercado imobiliário. Ela possui um profundo conhecimento das opções de financiamento e está sempre disposta a ajudar os clientes a encontrar o imóvel ideal."

#### 5.3.2 Keywords (Palavras-chave)

**EXTREMAMENTE IMPORTANTE para seleção automática de agente!**

**Como funciona:**
- Cada linha = uma palavra-chave
- Quando o cliente envia uma mensagem, o sistema busca essas palavras
- O agente com mais matches é selecionado

**Sistema de Pontuação:**
- Cada keyword encontrada = +10 pontos
- Mensagens genéricas = +2 pontos base para todos
- Agente com maior score é selecionado

**Exemplos por tipo de agente:**

**Agente de Triagem:**
```
oi
olá
quem
começar
ajuda
falar
atendimento
```

**Agente de Vendas:**
```
comprar
vender
compra
adquirir
venda
preço
valor
investir
```

**Agente de Locação:**
```
alugar
aluguel
locação
arrendar
alugo
inquilino
```

**Agente de Suporte:**
```
ajuda
suporte
problema
dúvida
informação
```

**DICA:** Use variações da mesma palavra (comprar, compra, compro, etc.)

#### 5.3.3 Instruções Personalizadas

Campo livre para instruções específicas do agente.

**Exemplo para Vendas:**
```
Destaque os benefícios de cada imóvel e mostre como ele pode atender às necessidades do cliente. Seja proativa em oferecer opções de financiamento e auxiliar o cliente em todo o processo de compra.
```

**Exemplo para Triagem:**
```
Priorize a coleta de informações essenciais para o direcionamento adequado. Seja cordial e mostre interesse genuíno nas necessidades do cliente.
```

#### 5.3.4 Persona

Descrição da personalidade e expertise do agente. Pode ser igual ao Backstory ou mais detalhada.

#### 5.3.5 Ferramentas Disponíveis

**📚 Usar base de conhecimento:**

Quando marcado:
- Agente terá acesso aos documentos carregados
- Poderá consultar informações automaticamente
- Mostrará checkboxes dos documentos disponíveis

**Como funciona:**
1. Marque "📚 Usar base de conhecimento"
2. Selecione quais documentos esse agente pode acessar
3. O agente consultará automaticamente quando necessário

**IMPORTANTE:**
- A consulta é feita AUTOMATICAMENTE quando o agente recebe uma mensagem
- Os resultados são adicionados ao contexto do agente
- O agente pode (mas nem sempre vai) usar essas informações na resposta

---

## 6. Base de Conhecimento

### 6.1 Como Funciona

A base de conhecimento permite que você:
1. Faça upload de documentos (PDF, TXT, DOCX, CSV, XLSX)
2. O sistema processa e divide em "chunks" (pedaços)
3. Cada chunk é vetorizado (transformado em números)
4. Quando o agente precisa de informação, busca nos chunks relevantes

### 6.2 Upload de Documentos

**Aba "Base de Conhecimento":**

1. Clique em "Escolher arquivo" ou arraste o arquivo
2. Formatos aceitos:
   - PDF (.pdf)
   - Word (.docx)
   - Texto (.txt)
   - Excel (.xlsx)
   - CSV (.csv)
3. Aguarde o upload e processamento
4. Documento aparecerá na lista com:
   - Nome do arquivo
   - Tamanho
   - Botão de deletar

**Processamento:**
```
Upload → Extração de texto → Divisão em chunks → Vetorização → Armazenamento
```

**Chunks:**
- Tamanho máximo: 1000 caracteres
- Overlap: 200 caracteres (para contexto)
- Cada chunk é indexado separadamente

### 6.3 Como o Agente Usa a Base

**Fluxo automático:**

1. Cliente envia mensagem
2. Agente é selecionado
3. **SE** agente tem "usar base de conhecimento" = true:
   - Sistema busca automaticamente na base usando a mensagem do cliente
   - Retorna os 3 chunks mais relevantes
   - Adiciona ao contexto do agente
4. Agente gera resposta (pode ou não usar o conhecimento)

**Busca por palavra-chave:**
- Compara palavras da mensagem com conteúdo dos chunks
- Calcula score baseado em matches
- Retorna chunks com maior score

**Exemplo:**
```
Mensagem: "Vc tem uma casa em curitiba pra vender?"
Palavras: ["vc", "tem", "uma", "casa", "em", "curitiba", "pra", "vender"]

Chunk 1: "Casa Bela Vista - 4 quartos, piscina - Curitiba - R$ 850.000"
Matches: "casa" (1x), "curitiba" (1x) = Score: 2

Chunk 2: "Apartamento Jardim Europa - Florianópolis - R$ 950.000"
Matches: nenhum = Score: 0

→ Chunk 1 é retornado ao agente
```

### 6.4 Isolamento por Crew

**IMPORTANTE:** Os documentos são isolados por crew!

- Documentos da Crew A não aparecem para Crew B
- Cada agente vê apenas os documentos da sua crew
- Filtrado automaticamente pelo `crewId`

### 6.5 Limitações da Base de Conhecimento

❌ **O que NÃO funciona:**
- Não garante que o agente USE a informação (depende do LLM)
- Busca por palavra-chave é limitada (não entende sinônimos)
- Chunks muito grandes podem perder contexto

✅ **O que funciona:**
- Upload e armazenamento de documentos
- Busca automática quando mensagem tem palavras-chave relevantes
- Filtragem por documento específico
- Isolamento por crew

---

## 7. Agentes de IA

### 7.1 Tipos de Agentes Recomendados

**1. Agente de Triagem**
- Primeiro contato com o cliente
- Coleta informações básicas
- Direciona para especialistas
- Keywords: oi, olá, ajuda, quem

**2. Agentes Especialistas**
- Foco em área específica (vendas, locação, suporte)
- Conhecimento profundo do domínio
- Keywords específicas da área

**3. Agente Padrão/Fallback**
- Ativado quando nenhum outro match
- Respostas genéricas
- Sem keywords (score sempre 0)

### 7.2 Boas Práticas para Agentes

**Nome:**
✅ "Ana - Especialista em Vendas"
❌ "Agente 1"

**Goal:**
✅ "Apresentar opções de imóveis para venda, fornecer informações sobre financiamento e auxiliar o cliente em todo o processo de compra."
❌ "Vender imóveis"

**Keywords:**
✅ Específicas e variadas: comprar, compra, vender, venda, adquirir
❌ Genéricas demais: casa, imóvel

**Backstory:**
✅ "Ana é uma especialista em vendas com 10 anos de experiência..."
❌ "Agente de vendas"

---

## 8. Guardrails (Regras de Comportamento)

### 8.1 O que são Guardrails?

Guardrails são **regras de comportamento** que orientam o agente sobre:
- O que ele DEVE fazer
- O que ele NÃO DEVE fazer

**IMPORTANTE:** Guardrails são **orientações fortes** mas não são **garantias absolutas**. O modelo de IA (Gemini) pode ocasionalmente ignorá-los.

### 8.2 Estrutura dos Guardrails

Cada agente tem dois tipos:

**DO (Fazer):**
- Comportamentos desejados
- Ações que deve tomar
- Como deve responder

**DON'T (Não Fazer):**
- Comportamentos proibidos
- O que evitar
- Limites de atuação

### 8.3 Como Escrever Guardrails Efetivos

**❌ RUIM - Vago e genérico:**
```
DO:
- use a base de conhecimento

DON'T:
- não seja rude
```

**✅ BOM - Específico e acionável:**
```
DO:
- Quando o cliente perguntar sobre produtos disponíveis, liste IMEDIATAMENTE todos os itens da base de conhecimento em formato de lista clara com nome, descrição e preço
- Sempre confirme o pedido antes de finalizar
- Use linguagem profissional mas amigável

DON'T:
- Nunca invente produtos que não estão na base de conhecimento
- Nunca prometa prazos de entrega sem confirmar disponibilidade
- Nunca peça informações pessoais sensíveis (CPF, senha, dados bancários)
```

### 8.4 Exemplos de Guardrails por Contexto

**Imobiliária - Vendas:**
```
DO:
- Quando o cliente perguntar sobre imóveis disponíveis, liste TODOS os imóveis da base de conhecimento que correspondem (tipo, cidade, bairro)
- Destaque características únicas de cada imóvel (piscina, garagem, área gourmet)
- Pergunte sobre orçamento somente APÓS mostrar opções
- Ofereça agendar visita quando cliente demonstrar interesse

DON'T:
- Nunca invente imóveis que não existem na base
- Nunca diga valores aproximados - use APENAS os valores da base
- Nunca prometa financiamento sem consultar especialista
```

**Restaurante:**
```
DO:
- Quando cliente pedir cardápio, mostre TODOS os itens da categoria solicitada (entrada, prato principal, sobremesa, bebida)
- Liste nome do prato, descrição breve e preço
- Pergunte sobre alergias antes de confirmar pedido
- Confirme endereço de entrega antes de finalizar

DON'T:
- Nunca invente pratos que não estão no cardápio
- Nunca altere preços - use apenas valores da base
- Nunca prometa tempo de entrega sem consultar cozinha
```

**Clínica - Agendamento:**
```
DO:
- Colete: nome completo, telefone, tipo de consulta desejada
- Verifique disponibilidade na agenda antes de confirmar
- Confirme data e hora com o cliente
- Envie mensagem de confirmação com todos os dados

DON'T:
- Nunca agende sem confirmar disponibilidade real
- Nunca dê diagnósticos ou orientações médicas
- Nunca peça informações médicas detalhadas (use apenas "motivo da consulta")
```

### 8.5 Guardrails e Base de Conhecimento

**IMPORTANTE:** Guardrails podem orientar o uso da base, mas não garantem:

**Guardrail típico:**
```
DO:
- quando o cliente disser que quer saber quais são os imóveis disponíveis, você deve usar a base de conhecimento e trazer os imóveis a venda
```

**Problema:** Muito vago. O agente pode:
- Interpretar que deve "usar" mas não necessariamente "listar"
- Pedir mais detalhes antes de listar
- Resumir ao invés de listar todos

**Solução - Guardrail específico:**
```
DO:
- Quando o cliente perguntar sobre produtos/imóveis/itens disponíveis, liste IMEDIATAMENTE todos os itens da base de conhecimento no formato:
  Nome | Descrição | Cidade/Categoria | Preço/Valor
- NÃO peça mais informações antes de mostrar a lista
- Após mostrar a lista completa, ENTÃO pergunte qual interessou mais

DON'T:
- Nunca pergunte preferências ANTES de mostrar os itens disponíveis
- Nunca resuma ou filtre a lista sem que o cliente peça
- Nunca invente itens que não estão na base de conhecimento
```

### 8.6 Priorização de Guardrails

O sistema adiciona os guardrails em **INSTRUÇÕES CRÍTICAS** no prompt:

```
INSTRUÇÕES CRÍTICAS (SIGA RIGOROSAMENTE):

🔴 OBRIGATÓRIO - Você DEVE:
  • [Guardrails DO aqui]

🚫 PROIBIDO - Você NÃO DEVE:
  • [Guardrails DON'T aqui]
```

Isso dá **prioridade alta** mas não é 100% garantido.

### 8.7 Limitações dos Guardrails

**Guardrails NÃO são regras de código:**
- São orientações para o modelo de IA
- O modelo pode interpretá-los de forma diferente
- Em casos raros, pode ignorá-los completamente

**Quando pode falhar:**
- Guardrails muito longos (modelo perde contexto)
- Guardrails contraditórios
- Situações não previstas nos guardrails

**Garantia aproximada:**
- Guardrails bem escritos: ~85-95% de adesão
- Guardrails vagos: ~60-70% de adesão

---

## 9. Ferramentas Disponíveis

### 9.1 Base de Conhecimento (consultar_base_conhecimento)

**Ativação:**
- Marque "📚 Usar base de conhecimento"
- Selecione documentos específicos (ou todos)

**Funcionamento:**
- Consulta automática quando agente recebe mensagem
- Busca por palavra-chave nos chunks
- Retorna top 3 resultados mais relevantes
- Adiciona ao contexto do agente

**Não é necessário configurar** - funciona automaticamente.

### 9.2 Outras Ferramentas (Futuras)

O sistema está preparado para:
- Google Sheets (cadastro, busca de clientes)
- Agendamento (calendário)
- Envio de imagens
- Webhooks customizados

*(Documentação será adicionada quando implementadas)*

---

## 10. Integração WhatsApp

### 10.1 Como Funciona

1. WhatsApp envia mensagem → Backend recebe
2. Backend identifica:
   - Número do cliente (`remoteJid`)
   - Tenant/Empresa
   - Crew ativa
3. Backend encaminha para CrewAI Service
4. CrewAI processa e retorna resposta
5. Backend envia resposta ao WhatsApp

### 10.2 Identificação de Cliente

O sistema identifica o cliente pelo **número do WhatsApp** (remoteJid):
- Formato: `5531994042943@s.whatsapp.net`
- Usado para manter histórico de conversa
- Usado para busca automática em ferramentas (Google Sheets)

### 10.3 Histórico de Conversa

- Armazenado automaticamente no Firestore
- Enviado ao agente para contexto
- Formato: alternado entre Cliente e Agente
- Limitado às últimas N mensagens (para não estourar contexto)

---

## 11. Deploy e Manutenção

### 11.1 Estrutura de Pastas

```
atendechat/
├── codatendechat-main/
│   ├── frontend/          # React app
│   ├── backend/           # Node.js API
│   └── crewai-service/    # Python FastAPI
├── deploy-local.sh        # Script de deploy
└── google-credentials.json # Credenciais GCP
```

### 11.2 Deploy Local (Da Máquina para VM)

**Script:** `deploy-local.sh`

**Pré-requisitos:**
1. Acesso SSH à VM configurado
2. Senha sudo da VM
3. Credenciais do Google Cloud em `google-credentials.json`

**Comando:**
```bash
bash deploy-local.sh
```

**O que o script faz:**

1. **Verifica credenciais** Google Cloud
2. **Pede senha sudo** da VM (usado para restart de serviços)
3. **Git pull** na VM (com stash de alterações locais)
4. **Frontend:**
   - Limpa cache (node_modules/.cache, build)
   - Instala dependências
   - Build de produção
   - Rsync para VM
5. **Backend:**
   - Copia package.json
   - Instala dependências na VM
   - Restart container Docker
6. **CrewAI Service:**
   - Copia credenciais GCP para /opt/crewai
   - Cria/atualiza virtualenv Python
   - Instala dependências (requirements.txt)
   - Mata processos antigos na porta 8000
   - Restart serviço systemd

**Tempo aproximado:** 5-10 minutos

### 11.3 Verificando o Deploy

**Frontend:**
```bash
# Na VM
ls -la /home/airton/atendechat/codatendechat-main/frontend/build/static/js/
# Verificar hash dos arquivos - deve mudar a cada deploy
```

**Backend:**
```bash
# Na VM
docker ps | grep backend
docker logs codatendechat-main-backend-1 --tail 50
```

**CrewAI Service:**
```bash
# Na VM
sudo systemctl status crewai.service
sudo journalctl -u crewai.service -n 50
```

### 11.4 Logs e Monitoramento

**Backend (Docker):**
```bash
docker logs codatendechat-main-backend-1 -f
```

**CrewAI Service:**
```bash
sudo journalctl -u crewai.service -f
```

**Logs importantes do CrewAI:**
- `✅ Dados da equipe carregados: [nome]` - Crew carregada com sucesso
- `🔍 INICIANDO SELEÇÃO DE AGENTE` - Começou processamento
- `✅ AGENTE SELECIONADO: [nome]` - Agente escolhido
- `🔍 Agente consultando base de conhecimento` - Buscando na base
- `✅ Encontrados X resultados` - Resultados da busca
- `📊 Total de chunks encontrados` - Debug da busca

### 11.5 Troubleshooting de Deploy

**Problema: Frontend não atualiza (mesmo hash)**
- Causa: Git pull falhou ou cache não foi limpo
- Solução: Verificar se deploy limpou cache e fez build novo

**Problema: CrewAI não inicia (porta 8000 em uso)**
- Causa: Processo antigo não foi morto
- Solução:
```bash
sudo lsof -ti:8000 | xargs sudo kill -9
sudo systemctl restart crewai.service
```

**Problema: Base de conhecimento não funciona**
- Verificar logs: `📊 Total de chunks encontrados na crew: 0`
- Causa: Chunks salvos com crewId errado ou sem crewId
- Solução: Deletar documento e fazer upload novamente

---

## 12. Troubleshooting

### 12.1 Agente Errado Sendo Selecionado

**Sintoma:** Cliente fala sobre vendas mas cai no agente de locação

**Causa:** Keywords não configuradas ou genéricas demais

**Solução:**
1. Edite a crew
2. Vá no agente correto
3. Adicione keywords específicas (uma por linha):
   ```
   vender
   venda
   comprar
   compra
   ```
4. Salve a crew
5. Teste novamente

**Como verificar no log:**
```
🔍 SELEÇÃO DE AGENTE PARA MENSAGEM: 'quero comprar'
   🤖 Analisando agente: Ana - Vendas
      Keywords configuradas: ['vender', 'comprar']
      ✅ Keyword 'comprar' encontrada! +10 pontos
      Score final: 10
```

### 12.2 Base de Conhecimento Retorna 0 Resultados

**Sintoma:**
```
🔍 Buscando por palavra-chave: 'tem casa em curitiba?'
📊 Total de chunks encontrados na crew: 0
```

**Causas possíveis:**

1. **Documento não foi vetorizado**
   - Verifique no Firestore collection `vectors`
   - Deve ter documentos com `crewId` igual ao da crew

2. **Chunks salvos com crewId errado**
   - Verifique no Firestore se chunks têm campo `crewId`
   - Se tiver `tenantId` ao invés de `crewId` = documento antigo
   - Solução: Deletar e fazer upload novamente

3. **Agente não tem documento selecionado**
   - Edite a crew → Agentes → Abra o agente
   - Verifique se "📚 Usar base de conhecimento" está marcado
   - Verifique se documento está selecionado (checkbox marcado)

4. **Palavras da query não estão no documento**
   - Busca por palavra-chave é literal
   - Se perguntar "imóvel" mas documento tem "casa" = não match
   - Solução: Use palavras que existem no documento

### 12.3 Agente Ignora Base de Conhecimento

**Sintoma:** Base retorna resultados mas agente não usa na resposta

**Causa:** Guardrails vagos ou ausentes

**Solução:** Adicione guardrail específico:
```
DO:
- Quando o cliente perguntar sobre produtos disponíveis, liste IMEDIATAMENTE todos os itens da base de conhecimento
- NÃO peça informações adicionais antes de mostrar a lista

DON'T:
- Nunca invente produtos que não estão na base
```

**Limitação:** Mesmo com guardrails, LLM pode ocasionalmente ignorar (5-15% dos casos)

### 12.4 Agente Inventa Informações

**Sintoma:** Agente cria produtos/imóveis que não existem

**Causa:**
1. Base de conhecimento não consultada
2. Guardrails ausentes ou vagos
3. LLM "alucina" informações

**Solução:**
1. Verificar se base está sendo consultada (logs)
2. Adicionar guardrail forte:
   ```
   DON'T:
   - NUNCA invente produtos, preços ou informações que não estão na base de conhecimento
   - Se não souber uma informação, diga "não tenho essa informação disponível"
   ```
3. Adicionar na descrição do agente:
   ```
   "Você DEVE usar APENAS informações da base de conhecimento. NUNCA invente dados."
   ```

### 12.5 Upload de Documento Falha

**Sintoma:** Upload retorna erro 500 ou 400

**Causas:**

1. **Arquivo vazio ou corrompido**
   - Verificar tamanho do arquivo
   - Tentar abrir o arquivo antes de upload

2. **Tipo de arquivo não suportado**
   - Aceitos: PDF, DOCX, TXT, CSV, XLSX
   - Verificar extensão do arquivo

3. **Erro no processamento de texto**
   - PDF sem texto (só imagens) = erro
   - Arquivo com encoding inválido

**Logs para verificar:**
```
📥 Upload recebido na API Python
   Arquivo: documento.pdf
   Content-Type: application/pdf
   Crew: 0bJAG1Sre7PVky9vIdfh
```

Se aparecer erro após isso, verificar:
```
sudo journalctl -u crewai.service -n 100
```

---

## 13. Boas Práticas

### 13.1 Nomenclatura

**Crews:**
- Use nomes descritivos e contextualizados
- ✅ "Equipe Imobiliária WhatsApp"
- ❌ "Crew 1"

**Agentes:**
- Formato: "Nome - Especialidade"
- ✅ "Ana - Especialista em Vendas"
- ✅ "Laura - Triagem"
- ❌ "Agente Vendas"

### 13.2 Estrutura de Equipe Recomendada

**Pequena (2-3 agentes):**
1. Agente de Triagem (primeiro contato)
2. Agente Especialista (função principal)
3. Agente de Suporte (dúvidas/problemas)

**Média (4-5 agentes):**
1. Triagem
2. Vendas
3. Pós-venda/Suporte
4. Especialista Técnico
5. Agendamento

**Grande (6+ agentes):**
- Dividir por departamentos
- Cada um com keywords muito específicas
- Triagem robusta para direcionamento

### 13.3 Keywords

**Regras de ouro:**
1. Mínimo 3-5 keywords por agente especialista
2. Triagem: keywords genéricas (oi, olá, ajuda)
3. Especialistas: keywords específicas do domínio
4. Incluir variações (comprar, compra, compro)
5. Evitar keywords compartilhadas entre agentes

### 13.4 Base de Conhecimento

**Tamanho dos documentos:**
- Ideal: 1-20 páginas por documento
- Máximo: ~100 páginas (processamento pode demorar)
- Muito grande: dividir em múltiplos documentos

**Organização:**
- Um documento por categoria
- Ex: "cardapio_entradas.pdf", "cardapio_principais.pdf"
- Facilita seleção por agente

**Conteúdo:**
- Prefira tabelas e listas estruturadas
- Evite muito texto corrido
- Seja específico (preços exatos, não "a partir de")

### 13.5 Guardrails

**Tamanho:**
- DO: 2-5 regras específicas
- DON'T: 2-5 proibições claras
- Muito longo = modelo perde contexto

**Especificidade:**
- Seja MUITO específico no que quer
- Use verbos de ação (liste, mostre, pergunte)
- Inclua formato desejado da resposta

**Evite:**
- Guardrails contraditórios
- Instruções muito genéricas
- Muitas regras (máximo 10 total)

---

## 14. Limitações e Considerações

### 14.1 Limitações Técnicas

**Base de Conhecimento:**
- ❌ Busca não entende sinônimos (casa ≠ imóvel)
- ❌ Busca por palavra-chave é limitada
- ❌ Documentos muito grandes podem perder contexto
- ✅ Funciona bem com listas e tabelas estruturadas

**Guardrails:**
- ❌ Não são regras absolutas de código
- ❌ LLM pode ignorar em ~5-15% dos casos
- ❌ Muito longos = modelo perde contexto
- ✅ Bem escritos têm ~85-95% de adesão

**Seleção de Agente:**
- ❌ Baseada apenas em keywords (não entende contexto)
- ❌ Mensagens muito curtas podem ter match incorreto
- ✅ Funciona bem com keywords específicas

**Processamento de IA:**
- ❌ Pode "alucinar" informações não reais
- ❌ Pode interpretar instruções de forma diferente
- ❌ Limitado pelo contexto (não lembra de tudo)
- ✅ Muito bom em seguir instruções claras

### 14.2 Considerações de Custo

**Google Cloud (Vertex AI):**
- Gemini AI: custo por token (entrada + saída)
- Embeddings: custo por processamento
- Firestore: custo por leitura/escrita

**Otimizações:**
- Guardrails concisos (menos tokens)
- Documentos menores (menos processamento)
- Histórico limitado (menos contexto)

### 14.3 Considerações de Privacidade

**Dados armazenados:**
- Conversas completas no Firestore
- Documentos carregados (com conteúdo)
- Metadados de clientes

**LGPD/Privacidade:**
- Não solicite dados sensíveis sem necessidade
- Configure guardrails para não pedir CPF, senhas, etc.
- Implemente política de retenção de dados

### 14.4 Escalabilidade

**Limite de crews:** Ilimitado
**Limite de agentes por crew:** Recomendado até 10
**Limite de documentos por crew:** Recomendado até 50
**Tamanho de documento:** Recomendado até 20MB

### 14.5 Manutenção Recomendada

**Semanal:**
- Revisar conversas e identificar falhas
- Ajustar guardrails se necessário
- Atualizar base de conhecimento

**Mensal:**
- Revisar keywords dos agentes
- Analisar taxa de seleção correta
- Otimizar prompts se necessário

**Trimestral:**
- Avaliar criação de novos agentes
- Revisar estrutura da crew
- Atualizar documentação da base

---

## Apêndices

### A. Glossário

**Crew:** Equipe de agentes de IA trabalhando juntos

**Agente:** Membro individual da crew com função específica

**Guardrails:** Regras de comportamento (do/don't)

**Base de Conhecimento:** Sistema de armazenamento e busca de documentos

**Chunk:** Pedaço de documento (max 1000 caracteres)

**Embedding:** Representação vetorial (numérica) de texto

**Score:** Pontuação para seleção de agente

**Keyword:** Palavra-chave para seleção de agente

**LLM:** Large Language Model (Gemini AI)

**Tenant:** Empresa/organização no sistema multi-tenant

**RemoteJid:** Identificador do WhatsApp (número + @s.whatsapp.net)

### B. Checklist de Configuração

**Ao criar uma nova crew:**

- [ ] Nome descritivo da crew
- [ ] Descrição clara do propósito
- [ ] Pelo menos 1 agente criado
- [ ] Agente de triagem com keywords genéricas
- [ ] Agentes especialistas com keywords específicas
- [ ] Cada agente tem goal claro
- [ ] Cada agente tem backstory
- [ ] Guardrails DO configurados (2-5 regras)
- [ ] Guardrails DON'T configurados (2-5 regras)
- [ ] Base de conhecimento: documentos carregados
- [ ] Base de conhecimento: agentes têm documentos selecionados
- [ ] Testado com mensagens reais

### C. Templates de Guardrails

**E-commerce:**
```
DO:
- Liste todos os produtos da categoria solicitada com nome, descrição e preço
- Pergunte sobre forma de pagamento após confirmação do pedido
- Confirme endereço de entrega antes de finalizar

DON'T:
- Nunca invente produtos ou preços
- Nunca prometa prazo sem consultar estoque
- Nunca solicite dados de cartão de crédito
```

**Clínica Médica:**
```
DO:
- Colete: nome, telefone, tipo de consulta
- Verifique agenda antes de confirmar horário
- Envie confirmação com data, hora e endereço

DON'T:
- Nunca dê diagnósticos ou orientações médicas
- Nunca confirme horário sem verificar agenda
- Nunca solicite informações detalhadas de saúde
```

**Restaurante:**
```
DO:
- Mostre cardápio completo quando solicitado
- Liste nome, descrição e preço de cada item
- Pergunte sobre alergias antes de confirmar
- Confirme endereço de entrega

DON'T:
- Nunca invente pratos ou preços
- Nunca altere valores do cardápio
- Nunca prometa tempo de entrega sem confirmar
```

### D. Contatos e Suporte

**Repositório:** https://github.com/Airton659/atendechat

**Documentação técnica:** Ver arquivos no repositório
- `README.md`
- `deploy-local.sh`
- Código fonte em `/codatendechat-main`

---

## Controle de Versão do Documento

**Versão:** 1.0
**Data:** 23 de Outubro de 2025
**Autor:** Claude (Anthropic) + José Airton
**Última atualização:** 23/10/2025

**Histórico de alterações:**
- v1.0 (23/10/2025): Versão inicial completa do guia

---

**FIM DO GUIA COMPLETO**
