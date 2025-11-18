# 🚀 Guia Rápido de Instalação - Sistema de Agendamento com Agentes

## Pré-requisitos

- ✅ Sistema Atendechat funcionando
- ✅ CrewAI Service rodando
- ✅ PostgreSQL configurado
- ✅ Google Cloud / Vertex AI configurado

## Passo a Passo

### 1. Copiar arquivo .env do CrewAI Service

```bash
cd crewai-service
cp .env.example .env
```

### 2. Configurar variáveis de ambiente

Edite o arquivo `.env`:

```bash
# Google Cloud / Vertex AI (já deve estar configurado)
GOOGLE_CLOUD_PROJECT=seu-projeto-id
GOOGLE_CLOUD_LOCATION=global
VERTEX_MODEL=gemini-2.0-flash-lite

# Configurações da API
PORT=8001
HOST=0.0.0.0
NODE_ENV=development

# ⭐ NOVO: Configurações de integração com Backend
BACKEND_URL=http://localhost:8000
SERVICE_TOKEN=crewai_service_secret_token_2024
```

### 3. Instalar dependências (se necessário)

```bash
# No diretório crewai-service
pip install crewai-tools langchain-google-vertexai
```

### 4. Criar agente de agendamentos

**Opção A: Via Seed (Recomendado)**

```bash
cd backend
npx sequelize-cli db:seed --seed 20251117000000-create-scheduling-agent
```

**Opção B: Via Interface**

1. Acesse a interface de Teams
2. Abra uma equipe existente
3. Adicione um novo agente com:
   - Nome: "Assistente de Agendamentos"
   - Keywords: `["agendar", "marcar", "agenda", "consulta", "horario"]`
   - Copie as configurações de [AGENTES-AGENDAMENTO.md](AGENTES-AGENDAMENTO.md#opção-b-via-interface)

### 5. Reiniciar serviços

```bash
# Terminal 1: Backend
cd backend
npm run dev

# Terminal 2: CrewAI Service
cd crewai-service
python main.py
```

### 6. Testar!

Envie uma mensagem via WhatsApp conectado:

```
Quero agendar uma consulta para amanhã às 14h
```

O agente deve responder:

```
✅ Agendamento criado com sucesso!
Sua consulta foi agendada para [data] às 14:00!
```

## Verificação

### Verificar se o agente foi criado

```sql
SELECT id, name, keywords
FROM "Agents"
WHERE name LIKE '%Agendamento%';
```

### Verificar logs do CrewAI

```bash
cd crewai-service
tail -f logs/app.log
```

Deve aparecer:
```
✅ Tools inicializadas: schedule_appointment
🔧 TOOL DETECTION: Intenção de agendamento detectada!
```

### Verificar agendamentos criados

```sql
SELECT *
FROM "Schedules"
WHERE status = 'PENDENTE'
ORDER BY "createdAt" DESC
LIMIT 5;
```

## Problemas Comuns

### "Tool schedule_appointment não encontrada"

**Causa:** Arquivo `tools/schedule_tool.py` não foi criado ou importação falhou

**Solução:**
```bash
cd crewai-service
ls -la tools/
# Deve mostrar: __init__.py, schedule_tool.py

# Testar importação
python -c "from tools.schedule_tool import ScheduleAppointmentTool; print('OK')"
```

### "Erro ao conectar com backend"

**Causa:** BACKEND_URL incorreta ou backend não está rodando

**Solução:**
```bash
# Verificar se backend está rodando
curl http://localhost:8000/health

# Verificar variável de ambiente
cd crewai-service
cat .env | grep BACKEND_URL
```

### "Agente não está detectando agendamentos"

**Causa:** Keywords não configuradas ou agente não está ativo

**Solução:**
```sql
-- Verificar keywords
SELECT name, keywords, "isActive"
FROM "Agents"
WHERE name LIKE '%Agendamento%';

-- Ativar agente se necessário
UPDATE "Agents"
SET "isActive" = true
WHERE name = 'Assistente de Agendamentos';
```

## Estrutura de Arquivos Criados/Modificados

### ✅ Novos Arquivos

```
crewai-service/
├── tools/
│   ├── __init__.py                              # ✅ NOVO
│   └── schedule_tool.py                         # ✅ NOVO
└── .env.example                                 # ✅ ATUALIZADO

backend/src/database/seeds/
└── 20251117000000-create-scheduling-agent.ts    # ✅ NOVO

/
├── AGENTES-AGENDAMENTO.md                       # ✅ NOVO
└── INSTALACAO-AGENDAMENTO.md                    # ✅ NOVO (este arquivo)
```

### 🔧 Arquivos Modificados

```
crewai-service/
├── crew_engine_real.py                          # 🔧 MODIFICADO
│   - Adicionado import de ScheduleAppointmentTool
│   - Adicionado _initialize_tools()
│   - Adicionado _detect_and_execute_tools()
│   - Modificado process_message() para aceitar contact_id
│   - Integração de tool_context no prompt
│
└── main_service.py                              # 🔧 MODIFICADO
    - Adicionado teamData em ProcessMessageRequest
    - Simplificado chamada de process_message()
```

## Próximos Passos

Após a instalação, consulte [AGENTES-AGENDAMENTO.md](AGENTES-AGENDAMENTO.md) para:

- 📚 Entender a arquitetura completa
- 💡 Ver exemplos de uso
- 🔧 Configurações avançadas
- 🐛 Troubleshooting detalhado
- 🚀 Features futuras

## Suporte

Em caso de dúvidas:
1. Verifique os logs: `crewai-service/logs/` e `backend/logs/`
2. Consulte a documentação completa: [AGENTES-AGENDAMENTO.md](AGENTES-AGENDAMENTO.md)
3. Verifique se todas as dependências estão instaladas

---

**Boa sorte! 🎉**
