# 📘 MANUAL COMPLETO DO ADMINISTRADOR - AtendecChat AI

**Para pessoas SEM conhecimento técnico**
Versão: 1.0 | Data: 26/10/2025

---

## 📋 ÍNDICE

1. [O que é o Sistema](#1-o-que-é-o-sistema)
2. [Como Funciona (Explicação Simples)](#2-como-funciona-explicação-simples)
3. [Criando uma Equipe](#3-criando-uma-equipe)
4. [Configurando Agentes](#4-configurando-agentes)
5. [Base de Conhecimento](#5-base-de-conhecimento)
6. [Sistema de Validações](#6-sistema-de-validações)
7. [Exemplos Práticos por Tipo de Negócio](#7-exemplos-práticos-por-tipo-de-negócio)
8. [Erros Comuns e Como Resolver](#8-erros-comuns-e-como-resolver)

---

## 1. O QUE É O SISTEMA

### Sistema de Atendimento com Inteligência Artificial

Imagine que você tem uma equipe de atendentes virtuais (robôs) que conversam com seus clientes pelo WhatsApp. Cada "robô" (chamamos de **Agente**) tem uma personalidade e sabe fazer coisas específicas.

**O que o sistema faz:**
- ✅ Responde clientes automaticamente 24/7
- ✅ Consulta informações da sua empresa (Base de Conhecimento)
- ✅ Agenda compromissos
- ✅ Envia arquivos (catálogos, cardápios, etc)
- ✅ Valida se está dando informações corretas

**Exemplo prático:**
Cliente pergunta: "Tem consulta de cardiologia na quarta?"
Sistema consulta a base → Vê que cardiologista só atende segundas
Agente responde: "O cardiologista atende apenas às segundas-feiras, posso agendar para você?"

---

## 2. COMO FUNCIONA (EXPLICAÇÃO SIMPLES)

### Estrutura Hierárquica

```
EMPRESA (você)
  └── EQUIPE (ex: "Atendimento Clínica")
       ├── AGENTE 1 (ex: "Recepcionista")
       ├── AGENTE 2 (ex: "Agendador")
       └── AGENTE 3 (ex: "Suporte")

       BASE DE CONHECIMENTO
       ├── Arquivo 1: Horários de atendimento.pdf
       ├── Arquivo 2: Tabela de preços.txt
       └── Arquivo 3: Perguntas frequentes.docx
```

### Fluxo de uma Conversa

1. **Cliente envia mensagem** no WhatsApp
2. **Sistema escolhe qual agente** vai responder (baseado em palavras-chave)
3. **Agente consulta a Base de Conhecimento** (se necessário)
4. **Validações verificam** se a resposta está correta
5. **Agente responde** o cliente com informação precisa

---

## 3. CRIANDO UMA EQUIPE

### Passo a Passo

1. **Acesse o painel administrativo** do sistema
2. Clique em **"Equipes"** no menu lateral
3. Clique no botão **"+ Nova Equipe"**
4. Preencha:

#### **Nome da Equipe**
- **O que é:** Nome para identificar internamente
- **Exemplo:** "Atendimento Clínica São Lucas"
- **Dica:** Use um nome que deixe claro qual é o propósito

#### **Descrição**
- **O que é:** Explique para que serve essa equipe
- **Exemplo:** "Equipe responsável por agendar consultas e tirar dúvidas sobre a clínica"
- **Dica:** Seja específico, isso ajuda você a organizar múltiplas equipes

5. Clique em **"Criar"**

✅ **Pronto! Agora você tem uma equipe.**
⚠️ **Importante:** A equipe ainda não faz nada. Você precisa adicionar **Agentes**.

---

## 4. CONFIGURANDO AGENTES

### O que é um Agente?

Um agente é como um **funcionário virtual** com uma função específica. Cada agente tem:
- 🧑 **Personalidade** (formal, amigável, técnico)
- 🎯 **Função** (agendar, informar, vender)
- 📚 **Conhecimento** (o que ele pode consultar)
- ⚙️ **Ferramentas** (o que ele pode fazer)

---

### 4.1 Informações Básicas do Agente

#### **Nome do Agente**
- **O que é:** Como você vai identificar ele
- **Exemplos:**
  - "Maria - Recepcionista"
  - "João - Agendador"
  - "Suporte Técnico"
- **Dica:** Use nomes que deixem claro a função

#### **Função (Role)**
- **O que é:** O "cargo" do agente, em 1 frase curta
- **Exemplos Corretos:**
  - ✅ "Recepcionista virtual da clínica"
  - ✅ "Especialista em agendamentos médicos"
  - ✅ "Atendente de suporte técnico"
- **Exemplos ERRADOS:**
  - ❌ "Fazer várias coisas" (muito vago)
  - ❌ "Ajudar" (não diz o que faz)

#### **Objetivo (Goal)**
- **O que é:** O que o agente quer ALCANÇAR nas conversas
- **Exemplos Corretos:**
  - ✅ "Agendar consultas de forma rápida e sem erros"
  - ✅ "Responder dúvidas sobre preços e disponibilidade"
  - ✅ "Resolver problemas técnicos dos clientes"
- **Exemplos ERRADOS:**
  - ❌ "Ser legal" (muito vago)
  - ❌ "Atender bem" (não diz o objetivo específico)

#### **História (Backstory)**
- **O que é:** O "contexto" do agente, quem ele é
- **Tamanho:** 2-3 frases
- **Exemplos Corretos:**
  - ✅ "Você trabalha há 5 anos como recepcionista em clínicas médicas. Tem experiência em lidar com pacientes ansiosos e sabe a importância de passar calma e confiança. Conhece todos os procedimentos de agendamento da clínica."
  - ✅ "Você é especialista em suporte de internet banda larga. Já resolveu milhares de problemas de conexão e sabe guiar clientes passo a passo, mesmo os que não entendem nada de tecnologia."
- **Exemplos ERRADOS:**
  - ❌ "Você é um assistente" (muito genérico)
  - ❌ "Ajuda clientes" (não dá contexto)

**💡 DICA DE OURO:**
Quanto mais específico o Backstory, melhor o agente vai se comportar!

---

### 4.2 Palavras-Chave (Keywords)

#### **O que é**
São palavras que fazem o sistema escolher ESSE agente específico para responder.

#### **Como usar**
- Coloque **uma palavra por linha**
- Use palavras que os clientes realmente digitam
- Pense em sinônimos e variações

#### **Exemplo - Agente Agendador:**
```
agendar
marcar consulta
horário
disponibilidade
dia
hora
vaga
marcar
remarcar
desmarcar
```

#### **Exemplo - Agente Suporte:**
```
problema
não funciona
erro
bug
ajuda
não consigo
travou
```

**💡 DICA:**
Quanto mais palavras-chave, maior a chance de pegar a mensagem certa!

---

### 4.3 Personalidade

#### **Tom de Voz**
Escolha um:
- **Formal:** Para clínicas, escritórios, bancos
  - Exemplo: "Bom dia! Como posso auxiliá-lo?"
- **Amigável:** Para lojas, restaurantes, serviços gerais
  - Exemplo: "Oi! Como posso te ajudar hoje?"
- **Casual:** Para produtos jovens, startups, tech
  - Exemplo: "E aí! Bora resolver isso?"

#### **Instruções Personalizadas**
Aqui você pode adicionar comportamentos específicos.

**Exemplos:**
```
SEMPRE pergunte o nome completo do cliente antes de agendar.
NUNCA dê desconto sem autorização prévia.
Se o cliente estiver irritado, peça desculpas primeiro.
Sempre confirme o horário duas vezes para evitar erros.
```

---

### 4.4 Guardrails (Regras de Segurança)

#### **O que NÃO DEVE fazer (Don't)**
Lista de coisas **PROIBIDAS**.

**Exemplo - Clínica Médica:**
```
NÃO dê diagnósticos médicos
NÃO receite medicamentos
NÃO confirme agendamentos sem verificar disponibilidade
NÃO dê informações de outros pacientes
NÃO aceite pagamento fora do sistema oficial
```

**Exemplo - E-commerce:**
```
NÃO ofereça descontos não autorizados
NÃO prometa prazos de entrega que não podemos cumprir
NÃO aceite devoluções fora da política
```

#### **O que DEVE fazer (Do)**
Lista de comportamentos **OBRIGATÓRIOS**.

**Exemplo - Clínica Médica:**
```
SEMPRE consulte a base de conhecimento antes de responder sobre horários
SEMPRE pergunte CPF e telefone para agendamentos
SEMPRE confirme os dados antes de finalizar
SEMPRE seja empático com clientes preocupados
```

**Exemplo - E-commerce:**
```
SEMPRE pergunte CEP antes de calcular frete
SEMPRE informe prazo de entrega
SEMPRE ofereça rastreamento do pedido
```

**💡 REGRA DE OURO:**
Guardrails são a coisa MAIS IMPORTANTE! Se você configurar bem aqui, evita 90% dos problemas.

---

### 4.5 Persona

#### **O que é**
É um texto maior que define a "alma" do agente. Você pode repetir informações do Backstory aqui, mas de forma mais detalhada.

**Template sugerido:**
```
Você é [nome/função] da empresa [nome da empresa].

Sua personalidade:
- [Característica 1]
- [Característica 2]
- [Característica 3]

Seu jeito de falar:
- [Como você se expressa]
- [Palavras que usa]
- [O que evita falar]

Seu conhecimento:
- [O que você sabe muito bem]
- [Em que você é especialista]

Como você resolve problemas:
- [Seu processo passo a passo]
```

**Exemplo Preenchido - Recepcionista de Clínica:**
```
Você é a Maria, recepcionista da Clínica São Lucas.

Sua personalidade:
- Paciente e acolhedora
- Organizada e detalhista
- Calma mesmo em situações de estresse
- Sempre positiva e sorridente (mesmo que seja texto!)

Seu jeito de falar:
- Usa "você" ao invés de "senhor/senhora" (mas com respeito)
- Usa emojis sutis quando adequado (😊, ✅, 📅)
- Confirma informações importantes duas vezes
- Evita termos muito técnicos médicos

Seu conhecimento:
- Sabe todos os horários de todos os médicos
- Conhece os planos de saúde aceitos
- Sabe explicar preparos para exames
- Conhece a localização exata da clínica

Como você resolve problemas:
- Sempre consulta a base de conhecimento primeiro
- Se não souber, avisa: "Vou verificar e já te retorno"
- Em casos de urgência, orienta ir ao pronto-socorro
- Confirma agendamentos com: data + hora + médico + especialidade
```

**💡 DICA:**
Copie o template acima e preencha para o SEU negócio!

---

### 4.6 Ferramentas (Tools)

Marque as caixinhas conforme o que o agente pode fazer:

#### ☑️ **Pode consultar Base de Conhecimento**
- **Quando usar:** Sempre! Todo agente deve ter isso.
- **O que faz:** Agente pode ler os documentos que você enviou.

#### ☑️ **Pode agendar compromissos**
- **Quando usar:** Se seu negócio trabalha com agendamentos (clínicas, salões, consultorias).
- **O que faz:** Agente pode criar agendamentos no sistema.
- **⚠️ Atenção:** Agendamento fica PENDENTE até você confirmar manualmente!

#### ☑️ **Pode enviar arquivos (File List)**
- **Quando usar:** Se você tem documentos para enviar aos clientes (cardápios, catálogos, contratos).
- **O que faz:** Agente pode enviar arquivos que você configurou na seção "Arquivos".

---

### 4.7 Seleção de Documentos

Aqui você escolhe **quais documentos** da Base de Conhecimento esse agente específico pode consultar.

**Por que isso é importante?**
- Agente de vendas não precisa acessar documentos internos de RH
- Agente de suporte não precisa acessar contratos comerciais

**Como configurar:**
1. Marque as caixinhas dos documentos relevantes
2. Se marcar TODOS, o agente pode acessar tudo
3. Se não marcar nenhum, ele não consegue consultar nada (ruim!)

**💡 DICA:**
Em caso de dúvida, marque TODOS os documentos. Depois você pode refinar.

---

## 5. BASE DE CONHECIMENTO

### O que é

É a "biblioteca" da sua empresa. Tudo que você colocar aqui, os agentes podem consultar para responder os clientes.

### Tipos de Arquivos Aceitos

- ✅ PDF
- ✅ TXT (texto simples)
- ✅ DOC / DOCX (Word)

### O que colocar na Base

#### **Obrigatórios (todo negócio precisa):**
1. **Horários de funcionamento**
2. **Endereço e contatos**
3. **Produtos/Serviços oferecidos**
4. **Preços e condições de pagamento**
5. **Políticas (devolução, cancelamento, etc)**

#### **Recomendados:**
6. **Perguntas frequentes** (FAQ)
7. **Instruções de uso** (se aplicável)
8. **Diferenciais da empresa**
9. **Promoções vigentes**

#### **Avançado:**
10. **Scripts de atendimento** (como responder situações específicas)
11. **Tabelas de produtos** (nome, código, preço)
12. **Calendário de eventos/feriados**

---

### Como Criar Bons Documentos

#### **Formato Ideal para Horários**
```
HORÁRIOS DE ATENDIMENTO

Segunda-feira: 8h às 18h
Terça-feira: 8h às 18h
Quarta-feira: 8h às 18h
Quinta-feira: 8h às 18h
Sexta-feira: 8h às 17h
Sábado: 9h às 13h
Domingo: FECHADO

ESPECIALIDADES POR DIA:

Cardiologista: Apenas segundas-feiras (8h às 12h)
Dermatologista: Terças e quintas-feiras (14h às 18h)
Ortopedista: Quartas-feiras (9h às 13h)
```

**Por que esse formato funciona?**
- Informação clara e direta
- Fácil para a IA buscar
- Sem ambiguidades

#### **Formato Ideal para Preços**
```
TABELA DE PREÇOS - Atualizada em 26/10/2025

Consulta Cardiologia: R$ 350,00
Consulta Dermatologia: R$ 280,00
Consulta Ortopedia: R$ 320,00

Exame Eletrocardiograma: R$ 180,00
Exame Raio-X Tórax: R$ 150,00

CONVÊNIOS ACEITOS:
- Unimed
- Bradesco Saúde
- SulAmérica

NÃO aceitamos Amil nem NotreDame.
```

#### **Formato Ideal para FAQ**
```
PERGUNTAS FREQUENTES

P: Aceitam cartão de crédito?
R: Sim, aceitamos Visa, Mastercard e Elo em até 3x sem juros.

P: Preciso de pedido médico para consulta?
R: Não, você pode agendar direto sem pedido.

P: Posso remarcar uma consulta?
R: Sim, com até 24h de antecedência sem custo.

P: Tem estacionamento?
R: Sim, temos estacionamento gratuito para pacientes.
```

---

### ⚠️ Erros Comuns na Base de Conhecimento

#### ❌ **ERRO 1: Informação desatualizada**
```
Problema: Documento diz "Consulta R$ 200" mas já subiu para R$ 250
Solução: SEMPRE atualize os documentos quando algo mudar
```

#### ❌ **ERRO 2: Informações contraditórias**
```
Problema: Um doc diz "Atendemos sábado" e outro diz "Não atendemos sábado"
Solução: Revise TODOS os documentos e garanta consistência
```

#### ❌ **ERRO 3: Texto muito técnico**
```
Problema: "Procedimento de revascularização miocárdica..."
Solução: Use linguagem simples: "Cirurgia do coração para desobstruir artérias"
```

#### ❌ **ERRO 4: Informação vaga**
```
Problema: "Atendemos de segunda a sexta"
Solução: "Atendemos de segunda a sexta das 8h às 18h"
```

---

## 6. SISTEMA DE VALIDAÇÕES

### O que é (Explicação Simples)

Imagine que você tem um **fiscal** que fica olhando o que o agente vai responder ANTES de enviar ao cliente. Se o agente estiver prestes a dar uma informação errada, o fiscal corrige na hora.

**Exemplo real:**
```
Cliente: "Quero agendar cardiologia na quarta"

SEM VALIDAÇÃO:
Agente: "Ok, vou agendar cardiologia para quarta!"
❌ ERRO! Cardiologista não atende quartas.

COM VALIDAÇÃO:
Sistema detecta: "quarta" + "cardiologia"
Sistema busca na base: "Cardiologista atende segundas"
Sistema injeta correção no agente
Agente: "O cardiologista atende apenas às segundas-feiras.
         Posso agendar para segunda?"
✅ CORRETO!
```

---

### Como Configurar Validações

#### **Passo 1: Acesse a Aba Validações**
1. Entre na edição da equipe
2. Clique na aba **"Validações"**
3. Escolha qual agente você quer configurar (tem um menu dropdown)

#### **Passo 2: Ativar o Sistema**
- Ligue o **switch "Sistema Ativado"** no topo
- Quando desligado, nenhuma validação funciona

#### **Passo 3: Criar uma Regra**
Clique em **"Adicionar Nova Regra"**

---

### Configurando uma Regra (Passo a Passo)

#### **ABA 1: BÁSICO**

**Nome da Regra**
- **O que é:** Um nome para você identificar
- **Exemplo:** "Validar horários de especialidades médicas"

**Descrição**
- **O que é:** Explique o objetivo dessa regra
- **Exemplo:** "Garante que o agente não vai agendar especialidades em dias errados"

**Regra Ativada**
- Deixe ligado para funcionar

---

#### **ABA 2: TRIGGERS (Gatilhos)**

**O que são:** Palavras que ATIVAM essa validação.

**Quando o cliente usar essas palavras, o sistema vai validar.**

**Exemplo - Regra de Agendamento:**
```
agendar
marcar
consulta
horário
dia
```

**Como funciona:**
- Cliente diz: "Quero marcar uma consulta"
- Sistema vê a palavra "marcar" → ATIVA a validação
- Sistema verifica se os dados estão corretos antes do agente responder

💡 **DICA:** Coloque MUITAS palavras-gatilho! Quanto mais, melhor.

---

#### **ABA 3: ENTIDADES (Extração)**

**O que são:** Informações que o sistema vai "retirar" da mensagem do cliente e validar.

##### **Como Adicionar uma Entidade:**

1. **Tipo de Entidade**
   - **O que é:** Um nome para identificar o que você quer extrair
   - **Exemplos:**
     - `tipo_consulta`
     - `dia_semana`
     - `horario`
     - `produto`

2. **Método de Extração**
   Escolha um dos 3:

   **A) Keywords (Lista de Palavras)**
   - **Quando usar:** Quando você sabe EXATAMENTE quais são as opções
   - **Formato:** Liste separado por vírgula
   - **Exemplo:**
     ```
     Tipo: dia_semana
     Método: Keywords
     Padrão: segunda,terça,quarta,quinta,sexta,sábado,domingo
     ```
   - **O que faz:** Se o cliente disser "quarta", o sistema extrai "quarta"

   **B) Regex (Expressão Regular)**
   - **Quando usar:** Quando precisa buscar um padrão no texto
   - **⚠️ AVANÇADO:** Precisa conhecer expressões regulares
   - **Exemplo:**
     ```
     Tipo: tipo_consulta
     Método: Regex
     Padrão: consulta\s+(?:de\s+)?(\w+)
     ```
   - **O que faz:** Extrai "cardiologia" de "consulta de cardiologia"

   **C) Line Starts (Começo de Linha)**
   - **Quando usar:** Quando tem dados em formato de lista
   - **Exemplo:**
     ```
     Tipo: especialista
     Método: Line Starts
     Padrão: Especialista:
     ```
   - **O que faz:** Extrai tudo que vier depois de "Especialista:" no documento

3. **Descrição** (opcional mas recomendado)
   - Explique para que serve essa entidade

---

##### **EXEMPLO COMPLETO - Validação de Agendamento Médico:**

**ENTIDADE 1:**
```
Tipo: tipo_consulta
Método: Keywords
Padrão: cardiologia,dermatologia,ortopedia
Descrição: Tipo de especialidade médica
```

**ENTIDADE 2:**
```
Tipo: dia_semana
Método: Keywords
Padrão: segunda,terça,quarta,quinta,sexta,sábado,domingo
Descrição: Dia da semana desejado
```

**Como funciona:**
1. Cliente diz: "Quero consulta de cardiologia na quarta"
2. Sistema extrai:
   - `tipo_consulta` = "cardiologia"
   - `dia_semana` = "quarta"
3. Sistema busca na base: "cardiologia" + "quarta" existem juntos?
4. Base diz: "Cardiologia atende apenas segundas"
5. Sistema detecta CONFLITO
6. Injeta correção no agente
7. Agente responde corretamente

---

#### **ABA 4: AVANÇADO**

**Nível de Rigor**
- **Baixo:** Só avisa o agente, mas deixa ele decidir
- **Médio (RECOMENDADO):** Sugere correção com força
- **Alto:** Bloqueia resposta errada totalmente

**Auto-correção**
- ☑️ Ligado: Sistema corrige automaticamente
- ☐ Desligado: Sistema só alerta o agente

💡 **RECOMENDAÇÃO:** Use Médio + Auto-correção LIGADA

---

## 7. EXEMPLOS PRÁTICOS POR TIPO DE NEGÓCIO

### 7.1 CLÍNICA MÉDICA

#### **Equipe:** Atendimento Clínica

**AGENTE 1: Maria - Recepcionista**

```yaml
Função: Recepcionista virtual da clínica
Objetivo: Agendar consultas com precisão e tirar dúvidas sobre procedimentos
Backstory: |
  Você trabalha há 8 anos como recepcionista em clínicas.
  É extremamente organizada e nunca erra agendamentos.
  Sabe acalmar pacientes ansiosos e passar confiança.

Keywords:
  - consulta
  - agendar
  - marcar
  - horário
  - médico
  - doutor

Guardrails - NÃO DEVE:
  - NÃO dê diagnósticos médicos
  - NÃO receite medicamentos
  - NÃO confirme sem verificar disponibilidade na base
  - NÃO dê informações de outros pacientes

Guardrails - DEVE:
  - SEMPRE consulte a base de conhecimento ANTES de confirmar horários
  - SEMPRE pergunte nome completo, CPF e telefone
  - SEMPRE confirme especialidade + data + hora antes de finalizar
  - SEMPRE seja empática com pacientes preocupados

Ferramentas:
  ☑️ Consultar Base de Conhecimento
  ☑️ Agendar Compromissos
  ☐ Enviar Arquivos
```

**Base de Conhecimento:**
- `horarios-medicos.pdf`
- `especialidades.txt`
- `convenios-aceitos.txt`
- `localizacao-clinica.pdf`
- `faq-pacientes.txt`

**Validação 1: Horários de Especialidades**
```yaml
Triggers: agendar, marcar, consulta, horário
Entidades:
  - tipo_consulta: keywords (cardiologia,dermatologia,ortopedia)
  - dia_semana: keywords (segunda,terça,quarta,quinta,sexta)
Nível: Alto
```

---

### 7.2 RESTAURANTE

#### **Equipe:** Atendimento Restaurante

**AGENTE 1: Cardápio e Pedidos**

```yaml
Função: Atendente virtual do restaurante
Objetivo: Informar cardápio, receber pedidos e esclarecer dúvidas
Backstory: |
  Você trabalha há 5 anos em restaurantes.
  Conhece cada prato do cardápio de cor.
  Adora recomendar pratos baseado no gosto do cliente.

Keywords:
  - cardápio
  - prato
  - comida
  - pedir
  - delivery
  - entregar

Guardrails - NÃO DEVE:
  - NÃO ofereça pratos que não temos
  - NÃO prometa tempo de entrega menor que 50 minutos
  - NÃO aceite pagamento fora do sistema

Guardrails - DEVE:
  - SEMPRE pergunte o CEP para calcular frete
  - SEMPRE confirme o pedido completo antes de finalizar
  - SEMPRE informe tempo estimado de entrega
  - SEMPRE pergunte se tem alergia alimentar

Ferramentas:
  ☑️ Consultar Base de Conhecimento
  ☑️ Enviar Arquivos (cardápio em PDF)
  ☐ Agendar Compromissos
```

**Base de Conhecimento:**
- `cardapio-completo.pdf`
- `precos.txt`
- `area-entrega.txt`
- `tempo-preparo.txt`
- `pratos-veganos.txt`

---

### 7.3 ASSISTÊNCIA TÉCNICA

#### **Equipe:** Suporte Técnico

**AGENTE 1: Suporte Internet**

```yaml
Função: Especialista em suporte de internet banda larga
Objetivo: Resolver problemas de conexão rapidamente
Backstory: |
  Você tem 10 anos de experiência em suporte técnico.
  Já resolveu milhares de problemas de internet.
  Sabe explicar coisas técnicas de forma simples.

Keywords:
  - internet
  - wifi
  - conexão
  - lento
  - não funciona
  - problema

Guardrails - NÃO DEVE:
  - NÃO prometa técnico no mesmo dia se não tiver disponibilidade
  - NÃO peça dados sensíveis (senha do wifi) pelo chat
  - NÃO dê instruções complexas sem confirmar que o cliente entendeu

Guardrails - DEVE:
  - SEMPRE comece com soluções simples (reiniciar roteador)
  - SEMPRE pergunte qual luz está piscando no modem
  - SEMPRE valide se o problema foi resolvido antes de encerrar
  - SEMPRE ofereça agendamento de técnico se não resolver remotamente

Ferramentas:
  ☑️ Consultar Base de Conhecimento
  ☑️ Enviar Arquivos (manual do roteador)
  ☑️ Agendar Compromissos (visita técnica)
```

**Base de Conhecimento:**
- `guia-troubleshooting.pdf`
- `modelos-roteadores.txt`
- `problemas-comuns.txt`
- `quando-chamar-tecnico.txt`

---

## 8. ERROS COMUNS E COMO RESOLVER

### ❌ ERRO 1: Agente não responde nada

**Sintomas:**
- Cliente manda mensagem
- Sistema não responde

**Causas possíveis:**
1. Nenhum agente tem palavras-chave que batam com a mensagem
2. Base de conhecimento vazia
3. Sistema de validação bloqueou (rigor alto demais)

**Solução:**
1. Adicione MAS palavras-chave aos agentes
2. Crie um agente "Geral" com keywords genéricas:
   ```
   oi
   olá
   bom dia
   boa tarde
   ajuda
   info
   informação
   ```
3. Revise as validações e mude para rigor "médio"

---

### ❌ ERRO 2: Agente dá informação errada

**Sintomas:**
- Agente diz horários errados
- Agente confirma coisas que não existem

**Causas possíveis:**
1. Base de conhecimento desatualizada
2. Informação está escrita de forma ambígua
3. Validações não configuradas

**Solução:**
1. Atualize TODOS os documentos da base
2. Reescreva informações no formato claro (veja seção 5)
3. Configure validações para os casos críticos
4. Adicione guardrails "NÃO DEVE" específicos

---

### ❌ ERRO 3: Agente muito "robótico"

**Sintomas:**
- Respostas sem personalidade
- Cliente reclama que "parece bot"

**Causas possíveis:**
1. Persona mal configurada
2. Tom de voz muito formal
3. Falta de customização

**Solução:**
1. Reescreva a Persona (veja seção 4.5)
2. Mude o tom para "Amigável"
3. Adicione instruções personalizadas:
   ```
   Use emojis sutis quando adequado 😊
   Chame o cliente pelo nome
   Seja conversacional, não formal demais
   Mostre empatia quando o cliente estiver frustrado
   ```

---

### ❌ ERRO 4: Validações bloqueando tudo

**Sintomas:**
- Sistema não responde
- Logs mostram "validação bloqueou resposta"

**Causas possíveis:**
1. Rigor alto demais
2. Triggers pegando mensagens irrelevantes
3. Entidades muito restritivas

**Solução:**
1. Mude rigor para "Médio"
2. Seja mais específico nos triggers (não use "oi", "obrigado")
3. Revise as entidades e veja se estão cobrindo todos os casos

---

### ❌ ERRO 5: Agente não usa ferramentas

**Sintomas:**
- Agendamentos não são criados
- Arquivos não são enviados

**Causas possíveis:**
1. Ferramentas não foram marcadas
2. Instruções não mencionam as ferramentas
3. Guardrails bloqueando uso

**Solução:**
1. Verifique se as caixinhas estão marcadas
2. Adicione nas Instruções Personalizadas:
   ```
   Sempre que o cliente pedir para agendar, USE a ferramenta de agendamento.
   Quando perguntarem sobre cardápio/catálogo, ENVIE o arquivo.
   ```
3. Remova guardrails que impeçam uso das ferramentas

---

## 📝 CHECKLIST DE CONFIGURAÇÃO

Use esta lista para garantir que configurou tudo:

### ✅ Equipe
- [ ] Nome claro e descritivo
- [ ] Descrição explicando o propósito

### ✅ Agente (para cada um)
- [ ] Nome identificável
- [ ] Função (Role) em 1 frase clara
- [ ] Objetivo (Goal) específico
- [ ] Backstory com contexto (2-3 frases)
- [ ] Pelo menos 10 palavras-chave relevantes
- [ ] Guardrails "NÃO DEVE" (mínimo 3)
- [ ] Guardrails "DEVE" (mínimo 3)
- [ ] Persona detalhada (template preenchido)
- [ ] Ferramentas marcadas corretamente
- [ ] Documentos selecionados

### ✅ Base de Conhecimento
- [ ] Horários de funcionamento (atualizado!)
- [ ] Produtos/Serviços com preços
- [ ] Políticas importantes
- [ ] FAQ
- [ ] Todos os documentos em formato claro (veja seção 5)

### ✅ Validações (se aplicável)
- [ ] Sistema ativado
- [ ] Pelo menos 1 regra para casos críticos
- [ ] Triggers bem definidos
- [ ] Entidades configuradas
- [ ] Rigor adequado (médio recomendado)

---

## 🆘 PRECISA DE AJUDA?

### Se algo não funcionar:

1. **Verifique os logs do sistema**
   - Vá em "Logs" no painel
   - Procure por mensagens de erro
   - Copie o texto do erro

2. **Teste com mensagens simples**
   - Envie "oi" - deve responder
   - Envie uma palavra-chave do agente
   - Veja qual agente respondeu

3. **Revise a configuração**
   - Use o checklist acima
   - Compare com os exemplos da seção 7

4. **Entre em contato com suporte técnico**
   - Informe: qual equipe, qual agente, qual mensagem enviou
   - Envie print da configuração
   - Descreva o que esperava vs o que aconteceu

---

## 📚 RESUMO RÁPIDO

### Para começar do zero:

1. **Crie uma Equipe** com nome claro
2. **Adicione 1 Agente "Geral"** com muitas palavras-chave
3. **Configure os básicos:** Função, Objetivo, Backstory simples
4. **Adicione Guardrails** principais (3 DO + 3 DON'T)
5. **Suba 3 documentos** na Base: Horários, Preços, FAQ
6. **Marque "Consultar Base"** nas ferramentas
7. **TESTE** enviando mensagens reais

### Depois de testar:

8. Refine a Persona baseado nas respostas
9. Adicione mais agentes específicos
10. Configure validações para casos críticos
11. Adicione mais documentos conforme necessário

---

## ✅ DEPLOY - ESTÁ PRONTO?

**SIM!** Você pode fazer deploy. Mas:

### Antes do deploy, faça esses testes:

1. **Teste Básico:**
   ```
   Você: "oi"
   Deve: Agente responder normalmente
   ```

2. **Teste Palavra-Chave:**
   ```
   Você: [palavra-chave do agente]
   Deve: Agente específico responder
   ```

3. **Teste Base de Conhecimento:**
   ```
   Você: "Qual o horário de funcionamento?"
   Deve: Agente consultar base e responder certo
   ```

4. **Teste Ferramenta (se configurou agendamento):**
   ```
   Você: "Quero agendar para segunda às 10h"
   Deve: Sistema criar agendamento pendente
   ```

5. **Teste Validação (se configurou):**
   ```
   Você: [mensagem que deve dar erro, ex: "cardiologia na quarta"]
   Deve: Agente corrigir baseado na base
   ```

### Se TODOS os testes passaram:

🚀 **PODE FAZER DEPLOY!**

### Se algum teste falhou:

⚠️ **REVISE A CONFIGURAÇÃO** antes de colocar no ar.

---

**FIM DO MANUAL**

Versão 1.0 - 26/10/2025
© AtendecChat AI - Sistema de Atendimento Inteligente

---

💡 **LEMBRE-SE:** Configurar IA é como treinar um funcionário novo. No começo pode errar, mas com ajustes e feedback, vai melhorar muito!
