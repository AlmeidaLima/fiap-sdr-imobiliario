# Requisitos — Agente SDR Imobiliário com IA

## 1. Objetivo

Este documento registra os requisitos funcionais e não funcionais da POC do **Agente SDR Imobiliário com IA** desenvolvida para o Hackathon FIAP.

A solução deve demonstrar um fluxo de atendimento imobiliário assistido por inteligência artificial, desde o primeiro contato com o lead até sua qualificação, recomendação de imóveis e encaminhamento para atendimento humano.

---

## 2. Escopo da POC

A POC deverá demonstrar, de forma funcional, que um agente de IA consegue:

- conversar com um potencial cliente;
- compreender sua intenção;
- coletar informações relevantes;
- manter contexto entre mensagens;
- estruturar os dados do lead;
- identificar seu nível de interesse;
- consultar uma base de imóveis;
- apresentar imóveis compatíveis;
- realizar follow-up;
- permitir agendamento;
- gerar um resumo para o corretor.

O projeto não tem como objetivo reproduzir integralmente um CRM ou uma plataforma imobiliária de produção.

---

## 3. Personas

### 3.1. Lead

Pessoa interessada em:

- comprar imóvel;
- alugar imóvel;
- investir em imóveis.

O lead interage com o agente através de uma interface conversacional.

---

### 3.2. Corretor

Usuário que deverá receber informações estruturadas sobre os leads atendidos pela IA.

O corretor deverá conseguir identificar rapidamente:

- intenção;
- preferências;
- orçamento;
- urgência;
- imóveis apresentados;
- nível de qualificação;
- próxima ação.

---

## 4. Requisitos Funcionais

### RF001 — Iniciar atendimento

O sistema deve permitir que um lead inicie uma conversa com o agente.

Critérios de aceitação:

- o usuário consegue enviar uma mensagem;
- o agente consegue responder;
- a conversa possui um identificador;
- o histórico necessário pode ser recuperado durante o atendimento.

---

### RF002 — Identificar intenção do lead

O agente deve identificar a intenção principal do usuário.

Valores inicialmente suportados:

```text
COMPRA
ALUGUEL
INVESTIMENTO
INDEFINIDO
```

Critérios de aceitação:

- a intenção deve ser extraída da conversa quando possível;
- o agente não deve exigir que o usuário utilize termos específicos;
- quando não houver informação suficiente, deve solicitar esclarecimento.

---

### RF003 — Coletar dados para qualificação

O agente deve coletar progressivamente informações relevantes.

Campos iniciais:

```text
nome
intencao
tipo_imovel
cidade
regiao
orcamento_min
orcamento_max
quartos
urgencia
finalidade
```

Para investimento, poderão ser utilizados:

```text
ticket
expectativa_retorno
perfil_investidor
```

Critérios de aceitação:

- informações fornecidas espontaneamente devem ser aproveitadas;
- o agente deve perguntar apenas o que estiver ausente e for necessário;
- informações já fornecidas não devem ser solicitadas novamente sem motivo.

---

### RF004 — Manter contexto da conversa

O sistema deve manter o contexto necessário durante o atendimento.

Exemplo:

```text
Lead:
"Quero um apartamento em Águas Claras."

Agente:
"Qual o seu orçamento?"

Lead:
"Até 600 mil."

Agente:
"Quantos quartos você procura?"
```

O sistema deve manter:

```text
tipo_imovel = apartamento
regiao = Águas Claras
orcamento_max = 600000
```

Critérios de aceitação:

- informações anteriores continuam disponíveis;
- o agente não repete perguntas desnecessariamente;
- o estado estruturado do lead pode ser atualizado durante a conversa.

---

### RF005 — Persistir lead

O sistema deve persistir os dados estruturados do lead.

Critérios de aceitação:

- o lead deve possuir identificador único;
- informações coletadas devem poder ser atualizadas;
- o estado do lead deve poder ser recuperado posteriormente.

---

### RF006 — Persistir conversa

O sistema deve armazenar as mensagens necessárias para manter rastreabilidade e contexto.

Cada mensagem deve possuir, no mínimo:

```text
id
conversation_id
role
content
created_at
```

Roles esperadas:

```text
user
assistant
system
tool
```

A estrutura definitiva poderá ser ajustada durante a implementação.

---

### RF007 — Calcular Lead Score

O sistema deve calcular uma pontuação de qualificação do lead.

A lógica é determinística e utiliza o estado estruturado da conversa.

Regras:

```text
Intenção identificada      +20
Orçamento informado        +20
Região definida            +10
Urgência até 30 dias       +25
Urgência entre 31 e 90 dias +15
Aceitou reunião/visita     +25
```

Classificação inicial:

```text
0  - 39  → FRIO
40 - 69  → MORNO
70 - 100 → QUENTE
```

Critérios de aceitação:

- o cálculo deve ser realizado por código;
- o resultado deve ser reproduzível;
- o LLM não deve calcular ou alterar score e classificação;
- as regras devem poder ser testadas isoladamente;
- intenção comercial, urgência e aceite de reunião ou visita devem ser
  preservados entre turnos;
- negações e perguntas meramente informativas não devem produzir nova intenção
  ou aceite;
- urgências menores que um dia devem ser ignoradas;
- score e classificação não devem participar do routing ou determinar a busca
  de imóveis;
- score e classificação devem ser persistidos em `conversation.state`.

---

### RF008 — Consultar imóveis

O sistema deve permitir consultar uma base estruturada de imóveis.

Filtros inicialmente previstos:

```text
cidade
regiao
tipo_imovel
preco_min
preco_max
quartos
banheiros
area
finalidade
```

Critérios de aceitação:

- filtros devem ser aplicados sobre dados estruturados;
- resultados devem corresponder a registros existentes;
- o LLM não deve inventar imóveis;
- a consulta deve ser executada por uma operação controlada.

---

### RF009 — Importar base de imóveis

O sistema deve possuir mecanismo para importar uma base de imóveis para PostgreSQL.

Pipeline esperado:

```text
CSV
 ↓
Leitura
 ↓
Limpeza
 ↓
Normalização
 ↓
Validação
 ↓
Persistência
```

Critérios de aceitação:

- a importação deve ser reproduzível;
- registros inválidos devem ser identificáveis;
- transformações relevantes devem ser documentadas;
- quantidade importada deve poder ser validada.

---

### RF010 — Recomendar imóveis

O agente deve apresentar imóveis compatíveis com as preferências do lead.

Critérios de aceitação:

- recomendações devem vir da busca estruturada;
- imóveis inexistentes não devem ser apresentados;
- o agente pode explicar os resultados em linguagem natural;
- filtros utilizados devem corresponder às informações coletadas.

---

### RF011 — Utilizar RAG

O sistema poderá utilizar RAG para responder perguntas relacionadas a conhecimento textual.

Exemplos:

```text
informações sobre bairros
FAQs
financiamento
políticas
conteúdo imobiliário
documentação
```

Critérios de aceitação:

- documentos devem ser processados em chunks;
- embeddings devem ser armazenados no pgvector;
- consultas devem recuperar conteúdo relevante;
- a resposta deve utilizar o contexto recuperado quando aplicável;
- ausência de contexto suficiente não deve resultar em informação inventada.

---

### RF012 — Realizar follow-up

O sistema deve permitir acompanhamento de leads que não responderam ou não concluíram o atendimento.

Estados inicialmente planejados:

```text
NOVO
EM_ATENDIMENTO
AGUARDANDO_RESPOSTA
FOLLOWUP_1
FOLLOWUP_2
ENCERRADO
```

Critérios de aceitação:

- o estado deve ser persistido;
- follow-ups realizados devem ser registrados;
- mensagens duplicadas devem ser evitadas;
- leads encerrados não devem continuar recebendo follow-up automaticamente.

---

### RF013 — Agendar reunião ou visita

O sistema deve permitir registrar um agendamento.

Dados iniciais:

```text
lead_id
tipo
data
horario
status
observacao
```

Tipos:

```text
REUNIAO
VISITA
CONTATO
```

Critérios de aceitação:

- agendamento deve estar relacionado ao lead;
- data e horário devem ser registrados;
- o agente deve confirmar as informações antes de concluir o agendamento.

---

### RF014 — Gerar resumo para o corretor

O sistema deve gerar um resumo estruturado do atendimento.

O resumo poderá conter:

```text
nome do lead
intenção
tipo de imóvel
região
orçamento
quartos
urgência
lead score
classificação
imóveis apresentados
imóvel de interesse
agendamento
próxima ação
```

Critérios de aceitação:

- o resumo deve refletir informações realmente presentes no sistema;
- não deve inventar preferências;
- deve permitir entendimento rápido do caso.

---

### RF015 — Dashboard mínimo

O sistema deve possuir uma interface mínima para visualização dos leads.

Informações inicialmente previstas:

```text
nome
status
intenção
score
classificação
última interação
```

Ao visualizar um lead, devem poder ser apresentados:

```text
preferências
histórico
imóveis recomendados
resumo
agendamentos
```

O dashboard poderá ser simplificado para atender ao escopo da POC.

---

### RF016 — Integração com WhatsApp

A arquitetura deve permitir integração futura com WhatsApp através da Evolution API.

Critérios de aceitação da missão específica:

- receber mensagem;
- encaminhar mensagem ao backend;
- processar pelo agente;
- enviar resposta;
- relacionar conversa ao lead.

Essa funcionalidade não faz parte da fundação inicial.

---

### RF017 — Health Check

O backend deve possuir endpoint de health check.

Endpoint:

```text
GET /health
```

Resposta esperada:

```json
{
  "status": "ok",
  "service": "agente-sdr-imobiliario-api"
}
```

---

### RF018 — Documentação da API

O backend deve disponibilizar documentação automática através do Swagger do FastAPI.

Endpoint esperado:

```text
/docs
```

---

## 5. Requisitos Não Funcionais

### RNF001 — Execução padronizada

O projeto deve poder ser executado através de Docker Compose.

Comando esperado:

```bash
docker compose up --build
```

A execução deve iniciar, quando implementados:

```text
frontend
backend
postgres
```

---

### RNF002 — Testabilidade

A arquitetura deve permitir testes automatizados.

Backend:

```text
Pytest
```

Funcionalidades determinísticas devem ser preferencialmente testadas sem depender do LLM.

---

### RNF003 — Segurança de credenciais

Credenciais não devem ser versionadas.

Obrigatório:

```text
.env.example
```

Proibido versionar:

```text
.env
tokens
senhas
API keys
```

---

### RNF004 — Separação de responsabilidades

O backend deve respeitar as fronteiras definidas no `ARCHITECTURE.md`.

Fluxo padrão:

```text
Route
 ↓
Service
 ↓
Repository
 ↓
Database
```

Para IA:

```text
LangGraph
 ↓
Tool
 ↓
Service
 ↓
Repository
```

---

### RNF005 — Reprodutibilidade

Outro integrante deve conseguir clonar o projeto e iniciar o ambiente seguindo as instruções do README.

---

### RNF006 — Observabilidade

O sistema deve possuir logs suficientes para diagnosticar falhas relevantes.

Os logs não devem expor secrets.

---

### RNF007 — Desempenho

Por se tratar de uma POC utilizando LLM local, não é definido inicialmente um SLA rígido.

Entretanto:

- endpoints sem IA devem possuir resposta rápida;
- operações de banco não devem executar consultas desnecessárias;
- o tempo de resposta do LLM deverá ser medido durante os testes;
- gargalos relevantes deverão ser identificados antes da demonstração.

---

### RNF008 — Compatibilidade

A aplicação deverá ser executável através dos containers Docker definidos pelo projeto, reduzindo dependência da configuração local das máquinas dos integrantes.

---

### RNF009 — Manutenibilidade

O código deverá:

- ter responsabilidades claras;
- evitar duplicação desnecessária;
- possuir nomes compreensíveis;
- manter módulos pequenos;
- evitar abstrações prematuras.

---

### RNF010 — Qualidade das respostas da IA

O agente deve:

- manter coerência com o contexto;
- evitar inventar dados;
- assumir incerteza quando necessário;
- utilizar tools quando a informação depender de dados estruturados;
- utilizar contexto recuperado quando uma pergunta depender do RAG.

---

## 6. Requisitos de Dados

### Lead

Estrutura conceitual inicial:

```text
id
nome
intencao
tipo_imovel
cidade
regiao
orcamento_min
orcamento_max
quartos
urgencia
finalidade
score
classificacao
status
created_at
updated_at
```

---

### Property

Estrutura conceitual inicial:

```text
id
titulo
tipo_imovel
cidade
regiao
preco
quartos
banheiros
area
finalidade
descricao
origem
created_at
```

Os campos definitivos deverão ser adaptados ao dataset selecionado.

---

### Conversation

Estrutura conceitual:

```text
id
lead_id
status
created_at
updated_at
```

---

### Message

Estrutura conceitual:

```text
id
conversation_id
role
content
created_at
```

---

### Appointment

Estrutura conceitual:

```text
id
lead_id
tipo
data_hora
status
observacao
created_at
```

---

## 7. Fluxo Principal de Aceitação

O fluxo principal da POC deverá permitir demonstrar:

```text
Usuário inicia conversa
        ↓
Agente identifica intenção
        ↓
Agente coleta preferências
        ↓
Contexto é mantido
        ↓
Lead é qualificado
        ↓
Lead Score é calculado
        ↓
Imóveis são pesquisados
        ↓
Resultados são apresentados
        ↓
Usuário demonstra interesse
        ↓
Agendamento é realizado
        ↓
Resumo é gerado para o corretor
```

Esse será um dos principais fluxos utilizados para validar a solução.

---

## 8. Fora de Escopo Inicial

Não são objetivos obrigatórios da POC inicial:

- CRM completo;
- sistema financeiro;
- processamento de pagamentos;
- assinatura de contratos;
- integração com cartórios;
- autenticação corporativa complexa;
- alta disponibilidade;
- Kubernetes;
- arquitetura de microserviços;
- múltiplos bancos de dados;
- treinamento de modelo próprio;
- fine-tuning obrigatório;
- infraestrutura de produção completa.

Esses itens só devem ser incluídos caso exista justificativa específica.

---

## 9. Rastreabilidade

Sempre que possível, cada implementação deverá manter a relação:

```text
Requisito
   ↓
Código
   ↓
Teste
   ↓
Evidência
```

Exemplo:

```text
RF007 — Lead Score
       ↓
LeadScoreService
       ↓
test_lead_score.py
       ↓
Testes passando
```

---

## 10. Evolução dos requisitos

Este documento poderá evoluir durante o desenvolvimento.

Alterações relevantes devem:

- possuir justificativa;
- permanecer coerentes com `ARCHITECTURE.md`;
- ser refletidas nos testes;
- ser registradas antes de considerar a funcionalidade concluída.

Requisitos não devem ser alterados silenciosamente apenas para acomodar uma implementação existente.
