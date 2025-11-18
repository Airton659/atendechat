# 🗓️ Sistema de Agendamento com Agentes CrewAI

## Visão Geral

Este documento descreve como usar o sistema de integração entre agentes CrewAI e o calendário de agendamentos. Os agentes podem criar agendamentos automaticamente quando os usuários solicitarem via WhatsApp.

## Arquitetura

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐      ┌────────────┐
│  WhatsApp   │─────▶│   Backend    │─────▶│  CrewAI Service │─────▶│ PostgreSQL │
│             │      │   Node.js    │      │     Python      │      │            │
└─────────────┘      └──────────────┘      └─────────────────┘      └────────────┘
                            │                       │
                            │                       │
                            ▼                       ▼
                     ┌──────────────┐       ┌─────────────┐
                     │  Schedules   │       │    Tools    │
                     │   (Tabela)   │       │  schedule_  │
                     └──────────────┘       │ appointment │
                                            └─────────────┘
```

## Como Funciona

### 1. Fluxo Completo

1. **Usuário envia mensagem via WhatsApp:**
   ```
   "Quero agendar uma consulta para amanhã às 14h"
   ```

2. **Backend detecta que há uma equipe/agente configurado:**
   - Carrega os dados da equipe e agentes
   - Envia para CrewAI Service via API

3. **CrewAI Service processa:**
   - Seleciona agente apropriado por keywords
   - Detecta intenção de agendamento
   - Extrai informações (data, hora, descrição)
   - Executa tool `schedule_appointment`
   - Tool cria registro na tabela `Schedules`

4. **Agente responde ao usuário:**
   ```
   "✅ Sua consulta foi agendada para 18/11/2025 às 14:00!"
   ```

5. **Sistema de filas processa:**
   - BullQueue monitora agendamentos a cada 5 segundos
   - No horário programado, envia mensagem via WhatsApp

### 2. Detecção de Intenção

O sistema detecta automaticamente quando o usuário quer agendar algo através de **keywords**:

```python
schedule_keywords = [
    'agendar', 'marcar', 'agende', 'marque',
    'horario', 'horário', 'consulta',
    'compromisso', 'agenda', 'agendamento'
]
```

### 3. Extração de Informações

Quando detecta intenção de agendamento, o sistema usa IA para extrair:

- **Data e hora:** Suporta formatos naturais
  - "amanhã às 14h" → `2025-11-18T14:00:00`
  - "próxima segunda às 9h" → `2025-11-20T09:00:00`
  - "18/11 às 15:30" → `2025-11-18T15:30:00`

- **Descrição:** Motivo do agendamento
  - "consulta médica"
  - "corte de cabelo"
  - "reunião de alinhamento"

- **Validação:** Verifica se tem informação suficiente
  - Se falta algo, agente pergunta ao usuário

## Configuração

### 1. Variáveis de Ambiente

**CrewAI Service (`.env`):**
```bash
# Backend Node.js
BACKEND_URL=http://localhost:8000

# Token de autenticação entre services
SERVICE_TOKEN=crewai_service_secret_token_2024

# Google Cloud (Vertex AI)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
```

### 2. Criar Agente de Agendamentos

#### Opção A: Via Seed (Automático)

```bash
cd backend
npx sequelize-cli db:seed --seed 20251117000000-create-scheduling-agent
```

#### Opção B: Via Interface

Acesse a interface de gerenciamento de equipes e crie um agente com:

**Configurações Básicas:**
- **Nome:** Assistente de Agendamentos
- **Função:** Especialista em agendar consultas e compromissos
- **Objetivo:** Ajudar usuários a agendar de forma eficiente

**Keywords (importante!):**
```json
[
  "agendar", "marcar", "agenda", "agendamento",
  "consulta", "horario", "horário", "compromisso"
]
```

**Custom Instructions:**
```
Quando um usuário solicitar um agendamento:
1. Seja cordial e profissional
2. Colete data, horário e motivo de forma conversacional
3. Confirme TODAS as informações antes de criar
4. Use linguagem natural e amigável
```

**Do List:**
```json
[
  "Confirmar data, hora e motivo antes de agendar",
  "Usar linguagem natural e amigável",
  "Confirmar o agendamento criado com o usuário"
]
```

**Don't List:**
```json
[
  "Criar agendamento sem confirmar com o usuário",
  "Assumir informações que não foram fornecidas",
  "Agendar sem data/hora completa"
]
```

## Exemplos de Uso

### Exemplo 1: Agendamento Completo

**Usuário:**
```
Quero agendar uma consulta para amanhã às 14h
```

**Processo Interno:**
1. Keyword matching: ✅ "agendar" detectado
2. Extração:
   - Data/hora: `2025-11-18T14:00:00` ✅
   - Descrição: "consulta" ✅
   - Info completa: SIM ✅
3. Executa tool `schedule_appointment`
4. Cria registro no banco

**Agente Responde:**
```
✅ Agendamento criado com sucesso!
ID: 42
Data/Hora: 2025-11-18T14:00:00
Mensagem: consulta

Sua consulta foi agendada para 18/11/2025 às 14:00!
```

### Exemplo 2: Informação Incompleta

**Usuário:**
```
Quero marcar um horário
```

**Processo Interno:**
1. Keyword matching: ✅ "marcar", "horário" detectado
2. Extração:
   - Data/hora: ❌ Não informado
   - Descrição: ❌ Não informado
   - Info completa: NÃO ❌
3. Sistema identifica falta de informação

**Agente Responde:**
```
Claro! Ficaria feliz em ajudar a marcar um horário.
Para qual data e horário você gostaria de agendar?
```

**Usuário:**
```
Amanhã às 10h para cortar cabelo
```

**Agente Responde:**
```
✅ Perfeito! Agendamento criado para 18/11/2025 às 10:00 - corte de cabelo.
Até lá!
```

### Exemplo 3: Múltiplas Datas

**Usuário:**
```
Preciso agendar 3 consultas: segunda às 9h, quarta às 14h e sexta às 16h
```

**Agente Responde:**
```
Entendi! Vou agendar as 3 consultas para você:

1️⃣ Segunda-feira (20/11) às 9h
2️⃣ Quarta-feira (22/11) às 14h
3️⃣ Sexta-feira (24/11) às 16h

Confirma? Se sim, crio os 3 agendamentos.
```

## Estrutura de Arquivos

### Python (CrewAI Service)

```
crewai-service/
├── tools/
│   ├── __init__.py                  # Exporta tools
│   └── schedule_tool.py             # Tool de agendamento
├── crew_engine_real.py              # Motor principal (modificado)
├── main_service.py                  # API FastAPI (modificado)
└── .env.example                     # Template de configuração
```

### Backend (Node.js)

```
backend/src/
├── models/Schedule.ts               # Modelo existente
├── controllers/ScheduleController.ts # Controller existente
├── database/seeds/
│   └── 20251117000000-create-scheduling-agent.ts  # Seed do agente
└── services/WbotServices/
    └── wbotMessageListener.ts       # Já envia contactId
```

## API da Tool

### `ScheduleAppointmentTool`

**Método:** `_run(contact_id, message, send_at, company_id, user_id?)`

**Parâmetros:**
```python
{
    "contact_id": 123,           # ID do contato (obrigatório)
    "message": "Consulta médica", # Descrição (obrigatório)
    "send_at": "2025-11-18T14:00:00",  # ISO 8601 (obrigatório)
    "company_id": 1,             # ID da empresa (obrigatório)
    "user_id": 5                 # ID do usuário (opcional)
}
```

**Retorno (Sucesso):**
```
✅ Agendamento criado com sucesso!
ID: 42
Data/Hora: 2025-11-18T14:00:00
Mensagem: Consulta médica
```

**Retorno (Erro):**
```
❌ Erro ao criar agendamento: [mensagem de erro]
```

**Validações:**
- Data deve estar no futuro
- Formato ISO 8601 válido
- Contact ID deve existir
- Company ID deve existir

## Logs e Debugging

### Ativar Logs Detalhados

O sistema já tem logs integrados que aparecem no console do CrewAI Service:

```
🔧 TOOL DETECTION: Intenção de agendamento detectada!
📊 Dados extraídos: {'has_enough_info': True, 'send_at': '2025-11-18T14:00:00', ...}
✅ Tools inicializadas: schedule_appointment
```

### Verificar Agendamentos Criados

**SQL:**
```sql
SELECT * FROM "Schedules"
WHERE status = 'PENDENTE'
ORDER BY "sendAt" DESC
LIMIT 10;
```

**API:**
```bash
curl -X GET "http://localhost:8000/schedules" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Logs de Agentes

Os logs de execução são salvos automaticamente em `AgentLogs`:

```sql
SELECT
  al."createdAt",
  a."name" as agent_name,
  al."message",
  al."response",
  al."toolUsage"
FROM "AgentLogs" al
JOIN "Agents" a ON a.id = al."agentId"
WHERE al."toolUsage" IS NOT NULL
ORDER BY al."createdAt" DESC;
```

## Troubleshooting

### Problema: Tool não está sendo executada

**Verificar:**
1. Keywords do agente incluem termos de agendamento?
2. Logs mostram "TOOL DETECTION"?
3. SERVICE_TOKEN configurado?

**Solução:**
```bash
# Verificar keywords do agente
SELECT name, keywords FROM "Agents" WHERE "isActive" = true;

# Verificar logs do Python
tail -f crewai-service/logs/app.log

# Testar tool manualmente
python -c "from tools.schedule_tool import ScheduleAppointmentTool; print(ScheduleAppointmentTool())"
```

### Problema: Data sendo extraída incorretamente

**Causa:** LLM pode interpretar datas de forma diferente

**Solução:** Adicionar exemplos no custom instructions do agente:
```
Exemplos de interpretação de datas:
- "amanhã" = [data de amanhã]
- "próxima segunda" = [próxima segunda-feira]
- "daqui a 3 dias" = [data + 3 dias]
```

### Problema: Agendamento criado mas não enviado

**Verificar:**
1. Fila BullQueue está rodando?
2. Status do agendamento é "PENDENTE"?
3. `sendAt` está no futuro?

**Solução:**
```bash
# Verificar filas
curl http://localhost:8000/queues/status

# Reprocessar agendamentos
npx sequelize-cli db:seed --seed reprocess-schedules
```

## Próximos Passos

### Features Futuras

1. **Verificação de Disponibilidade:**
   - Checar conflitos de horário
   - Sugerir alternativas

2. **Reagendamento:**
   - Tool para modificar agendamentos
   - Cancelamento via agente

3. **Lembretes:**
   - Enviar lembrete X horas antes
   - Confirmação automática

4. **Integração com Calendários Externos:**
   - Google Calendar
   - Outlook Calendar
   - iCal

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs do CrewAI Service
2. Consulte a documentação do CrewAI: https://docs.crewai.com
3. Abra uma issue no repositório

---

**Versão:** 1.0.0
**Data:** 17/11/2025
**Autor:** Sistema CrewAI + Calendário
