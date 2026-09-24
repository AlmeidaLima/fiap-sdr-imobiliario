# Arquitetura — Agente SDR Imobiliário com IA

## 1. Objetivo

Este documento descreve a arquitetura da POC do **Agente SDR Imobiliário com IA**, desenvolvida para o Hackathon FIAP.

O objetivo da arquitetura é permitir:

- evolução incremental;
- separação clara de responsabilidades;
- testabilidade;
- manutenção simplificada;
- execução padronizada entre os integrantes;
- integração com modelos locais de IA;
- utilização de RAG;
- integração futura com WhatsApp;
- automação do processo de qualificação de leads.

A arquitetura deve permanecer simples o suficiente para uma POC, evitando complexidade desnecessária, mas organizada de forma que novas funcionalidades possam ser adicionadas sem necessidade de reestruturação completa do sistema.

---

## 2. Visão Geral

A solução será composta pelas seguintes tecnologias:

### Frontend

- React
- Next.js
- TypeScript

### Backend

- Python
- FastAPI

### Inteligência Artificial

- LangGraph para orquestração do agente;
- llama.cpp para execução local do modelo de linguagem;
- Qwen ou Gemma como modelos candidatos;
- RAG para recuperação de conhecimento;
- embeddings para busca semântica.

### Dados

- PostgreSQL;
- pgvector para armazenamento e busca de embeddings.

### Integrações

- Evolution API para integração futura com WhatsApp.

### Infraestrutura

- Docker;
- Docker Compose.

### Qualidade

- Pytest;
- testes unitários;
- testes de integração;
- validação automatizada das funcionalidades.

Arquitetura planejada:

```text
                   ┌─────────────────────┐
                   │       Usuário       │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │       Next.js       │
                   │       Frontend      │
                   └──────────┬──────────┘
                              │ HTTP
                              ▼
                   ┌─────────────────────┐
                   │       FastAPI       │
                   │       Backend       │
                   └──────────┬──────────┘
                              │
                   ┌──────────▼──────────┐
                   │      LangGraph      │
                   │ Orquestração Agente │
                   └──────────┬──────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
      ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
      │    Tools    │  │  llama.cpp  │  │     RAG     │
      │  do Agente  │  │     LLM     │  │  pgvector   │
      └──────┬──────┘  └─────────────┘  └──────┬──────┘
             │                                   │
             ▼                                   ▼
      ┌─────────────────────────────────────────────┐
      │                  Services                   │
      └──────────────────────┬──────────────────────┘
                             │
                             ▼
                   ┌─────────────────────┐
                   │     PostgreSQL      │
                   │     + pgvector      │
                   └─────────────────────┘
```

---

## 3. Estado Atual da Implementação

A arquitetura será implementada de forma incremental.

### Implementado

Atualmente estão implementados:

- estrutura inicial do repositório;
- backend FastAPI;
- frontend Next.js;
- endpoint `/health`;
- documentação Swagger;
- PostgreSQL;
- pgvector;
- Docker;
- Docker Compose;
- comunicação inicial entre frontend e backend;
- configuração inicial através de variáveis de ambiente.

### Planejado

Ainda serão implementados:

- persistência dos leads;
- persistência das conversas;
- base estruturada de imóveis;
- importação do dataset imobiliário;
- busca estruturada de imóveis;
- LangGraph;
- llama.cpp;
- modelo local de IA;
- memória conversacional;
- qualificação automática do lead;
- lead scoring;
- RAG;
- chunking;
- embeddings;
- busca vetorial;
- follow-up;
- agendamento;
- resumo para o corretor;
- dashboard;
- integração com Evolution API;
- integração com WhatsApp.

A presença de um componente neste documento não significa que ele já esteja implementado.

---

## 4. Organização do Backend

A estrutura planejada para o backend é:

```text
backend/
└── app/
    ├── agents/
    ├── api/
    ├── database/
    ├── integrations/
    ├── models/
    ├── rag/
    ├── services/
    ├── tools/
    ├── __init__.py
    └── main.py
```

Cada diretório possui uma responsabilidade específica.

### 4.1. api

Responsável pela exposição da aplicação através da API HTTP.

Deverá conter:

- endpoints;
- rotas;
- schemas de entrada;
- schemas de saída;
- validações relacionadas ao contrato HTTP.

Exemplo futuro:

```text
api/
├── health.py
├── leads.py
├── properties.py
└── conversations.py
```

As rotas devem permanecer simples.

Uma rota não deverá conter regras complexas de negócio.

Fluxo esperado:

```text
Request HTTP
     ↓
FastAPI Route
     ↓
Service
     ↓
Resposta
```

---

### 4.2. services

Responsável pelas regras de negócio da aplicação.

Exemplos futuros:

```text
LeadService
PropertyService
ConversationService
FollowUpService
SchedulingService
SummaryService
```

Os endpoints devem delegar regras de negócio para os services.

Exemplo:

```text
POST /leads
      ↓
LeadService
      ↓
Repository
      ↓
PostgreSQL
```

---

### 4.3. database

Responsável pela comunicação com PostgreSQL.

Deverá concentrar:

- configuração da conexão;
- gerenciamento de sessões;
- repositories;
- queries;
- persistência;
- acesso aos dados.

Fluxo:

```text
Service
   ↓
Repository
   ↓
PostgreSQL
```

O modelo de linguagem não deverá acessar diretamente o banco de dados.

---

### 4.4. models

Responsável pelos modelos de domínio e entidades persistidas.

Exemplos futuros:

```text
Lead
Property
Conversation
Message
Appointment
FollowUp
```

Esses modelos representarão as principais entidades utilizadas pelo sistema.

---

### 4.5. agents

Responsável pela lógica de orquestração dos agentes de IA.

A implementação prevista utilizará **LangGraph**.

O agente será responsável por:

- compreender a intenção do usuário;
- identificar informações já fornecidas;
- identificar informações ausentes;
- decidir qual pergunta realizar;
- decidir quais tools utilizar;
- manter o fluxo conversacional;
- solicitar busca de imóveis;
- solicitar cálculo do lead score;
- solicitar agendamento;
- produzir respostas naturais ao usuário.

O agente não deverá executar diretamente operações de persistência.

---

### 4.6. tools

Responsável por disponibilizar operações controladas que podem ser utilizadas pelo agente.

Exemplos futuros:

```text
buscar_imoveis()
consultar_lead()
salvar_preferencias()
calcular_lead_score()
agendar_visita()
consultar_disponibilidade()
```

O fluxo esperado é:

```text
LLM
 ↓
LangGraph
 ↓
Tool
 ↓
Service
 ↓
Repository
 ↓
PostgreSQL
```

Essa separação impede que o modelo tenha acesso irrestrito à infraestrutura da aplicação.

---

### 4.7. rag

Responsável pelo fluxo de **Retrieval-Augmented Generation (RAG)**.

Será utilizado principalmente para conhecimento não estruturado ou semiestruturado.

Exemplos:

- informações sobre bairros;
- descrições detalhadas de imóveis;
- FAQs;
- documentação;
- informações sobre financiamento;
- políticas da imobiliária;
- informações comerciais;
- orientações gerais relacionadas ao mercado imobiliário.

O RAG não deverá substituir consultas estruturadas ao banco de dados.

---

### 4.8. integrations

Responsável pelas integrações externas.

Exemplos planejados:

```text
Evolution API
llama.cpp
```

Integrações deverão permanecer isoladas atrás de adaptadores ou serviços específicos.

Exemplo:

```text
FastAPI
   ↓
LlmClient
   ↓
llama.cpp
```

ou:

```text
FastAPI
   ↓
WhatsAppService
   ↓
Evolution API
```

Isso evita que detalhes específicos de uma tecnologia sejam espalhados pela aplicação.

---

## 5. Separação entre SQL e RAG

Uma decisão importante da arquitetura é separar claramente:

```text
Dados estruturados
       ↓
PostgreSQL
```

de:

```text
Conhecimento textual
       ↓
RAG + pgvector
```

### 5.1. PostgreSQL

PostgreSQL deverá ser utilizado para informações objetivas e estruturadas.

Exemplos:

- preço;
- bairro;
- cidade;
- quantidade de quartos;
- quantidade de banheiros;
- vagas de garagem;
- área;
- tipo do imóvel;
- disponibilidade;
- finalidade;
- características estruturadas.

Exemplo:

```text
Usuário:

"Quero um apartamento de até R$ 600 mil,
com 3 quartos, em Águas Claras."

              ↓

Extração dos filtros

              ↓

tipo = apartamento
preco_max = 600000
quartos >= 3
regiao = Águas Claras

              ↓

PostgreSQL

              ↓

Imóveis compatíveis
```

A resposta objetiva sobre imóveis existentes deverá vir da base de dados.

O LLM não deverá inventar imóveis, preços ou características.

---

### 5.2. RAG

RAG deverá ser utilizado para conhecimento textual.

Exemplo:

```text
Usuário:

"Como é morar em Águas Claras?"

             ↓

Busca vetorial

             ↓

Chunks relevantes

             ↓

Contexto recuperado

             ↓

LLM

             ↓

Resposta contextualizada
```

Essa separação ajuda a reduzir respostas incorretas ou inventadas sobre os imóveis disponíveis.

---

## 6. Estratégia de RAG

O pipeline planejado será:

```text
Documentos
    ↓
Extração
    ↓
Normalização
    ↓
Chunking
    ↓
Embeddings
    ↓
pgvector
    ↓
Busca por similaridade
    ↓
Top-K chunks
    ↓
Contexto
    ↓
LLM
```

### 6.1. Chunking

Estratégia inicial:

```text
500 a 800 tokens por chunk
50 a 100 tokens de overlap
```

Essa configuração é apenas um ponto inicial e poderá ser alterada após testes.

Sempre que possível, deverá ser utilizado chunking estrutural ou semântico.

Exemplo:

```text
Documento
   ↓
Título
   ↓
Seção
   ↓
Subseção
   ↓
Chunks
```

---

### 6.2. Metadados

Os chunks deverão possuir metadados quando aplicável.

Exemplos:

```text
tipo_documento
bairro
cidade
categoria
origem
documento_id
chunk_index
```

Esses metadados poderão ser utilizados para combinar:

```text
filtros estruturados
        +
similaridade vetorial
```

permitindo uma busca híbrida.

---

### 6.3. Estrutura conceitual

Exemplo de estrutura futura:

```text
documentos_rag

id
documento_id
titulo
tipo_documento
conteudo
chunk_index
embedding
metadata
```

A estrutura definitiva será definida durante a implementação do RAG.

---

## 7. Modelo de Linguagem

O projeto utilizará execução local de LLM.

Tecnologia planejada:

```text
llama.cpp
```

Modelos candidatos:

```text
Qwen
Gemma
```

A escolha definitiva deverá ser realizada após benchmark.

Critérios:

- qualidade das respostas;
- capacidade de seguir instruções;
- qualidade em português;
- consumo de memória;
- velocidade;
- tamanho do modelo;
- compatibilidade com o hardware disponível;
- licença do modelo.

A licença do modelo escolhido deverá ser validada antes da utilização definitiva.

---

### 7.1. Execução do LLM

O llama.cpp deverá funcionar como um serviço independente.

Fluxo:

```text
FastAPI
   ↓
LangGraph
   ↓
Cliente LLM
   ↓
llama.cpp
   ↓
Modelo local
```

Isso permite trocar futuramente o modelo ou o mecanismo de inferência sem alterar toda a aplicação.

---

## 8. Qualificação do Lead

Uma das principais responsabilidades do agente será transformar uma conversa não estruturada em informações estruturadas.

Exemplo de dados:

```text
nome
intencao
tipo_imovel
regiao
orcamento_min
orcamento_max
quartos
urgencia
finalidade
score
status
```

Para investidores:

```text
ticket
expectativa_retorno
perfil_investidor
```

O agente deverá:

1. identificar informações fornecidas espontaneamente;
2. armazenar essas informações;
3. identificar quais informações ainda são necessárias;
4. perguntar somente o necessário;
5. evitar repetir perguntas;
6. manter o contexto da conversa.

Exemplo:

```text
Lead:
"Quero comprar um apartamento em Águas Claras
até 600 mil."

Agente identifica:

intencao = compra
tipo_imovel = apartamento
regiao = Águas Claras
orcamento_max = 600000

Informações ainda necessárias:

quartos
urgencia
```

O agente não deverá perguntar novamente informações que já foram fornecidas.

---

## 9. Lead Score

O lead scoring é determinístico.

A qualificação comercial é extraída por código e preservada no
`ConversationState`. Ela representa intenção de compra, aluguel ou investimento,
urgência normalizada em dias e aceite explícito de reunião ou visita. Negações,
perguntas meramente informativas e urgências menores que um dia não substituem
informações válidas já armazenadas.

O cálculo da pontuação é responsabilidade exclusiva do `LeadScoreService`. O
LLM não calcula nem altera score ou classificação.

Regras implementadas:

```text
Intenção identificada       +20
Orçamento informado         +20
Região definida             +10
Urgência até 30 dias        +25
Urgência entre 31 e 90 dias +15
Aceitou reunião/visita      +25
```

Classificação:

```text
0  - 39  → Frio
40 - 69  → Morno
70 - 100 → Quente
```

Exemplo:

```text
Lead
 │
 ├── intenção          +20
 ├── orçamento         +20
 ├── região            +10
 ├── urgência          +25
 └── aceitou visita    +25
                         ───
                         100

Resultado:
Lead Quente
```

O node `calculate_lead_score` recalcula a pontuação a cada turno, depois de
`process_message` e antes de `qualify_conversation`:

```text
START
  ↓
process_message
  ↓
calculate_lead_score
  ↓
qualify_conversation
  ↓
route_after_qualification
  ├── ask_question → generate_response → END
  └── search_properties → generate_response → END
```

O routing continua dependendo exclusivamente da qualificação mínima da conversa.
Score e classificação não determinam a busca de imóveis nem são utilizados como
filtros. `PropertySearchIntent` permanece separado de `commercial_intent`.

O resultado é mantido no `ConversationState` e persistido no JSON
`conversation.state`, sem alteração de schema do banco ou migration.

---

## 10. Follow-up

O sistema deverá possuir mecanismo de acompanhamento dos leads.

Fluxo inicial planejado:

```text
NOVO
  ↓
EM_ATENDIMENTO
  ↓
AGUARDANDO_RESPOSTA
  ↓
FOLLOWUP_1
  ↓
FOLLOWUP_2
  ↓
ENCERRADO
```

O mecanismo de follow-up deverá:

- manter contexto;
- saber qual foi a última interação;
- evitar mensagens duplicadas;
- evitar mensagens descontextualizadas;
- permitir encerramento do acompanhamento;
- registrar as tentativas realizadas.

O comportamento definitivo será definido durante a missão responsável pelo follow-up.

---

## 11. Agendamento

O agente deverá permitir o agendamento de:

- reuniões;
- contatos com corretor;
- visitas aos imóveis.

Para a POC, inicialmente poderá ser utilizada uma agenda simulada armazenada no próprio banco.

Exemplo:

```text
Lead demonstra interesse
          ↓
Agente oferece agendamento
          ↓
Lead escolhe data/horário
          ↓
Sistema valida disponibilidade
          ↓
Agendamento registrado
          ↓
Resumo enviado ao corretor
```

Integrações com calendários externos poderão ser avaliadas posteriormente, caso sejam necessárias.

---

## 12. Resumo para o Corretor

Após a qualificação do lead, o sistema deverá ser capaz de gerar um resumo estruturado.

Exemplo:

```text
Lead: João

Intenção:
Compra

Região:
Águas Claras

Tipo:
Apartamento

Orçamento:
Até R$ 600.000

Quartos:
3

Urgência:
Até 30 dias

Lead Score:
85 — Quente

Imóveis apresentados:
3

Interesse:
Imóvel #123

Próxima ação:
Visita agendada
```

Esse resumo deverá permitir que o corretor assuma o atendimento sem precisar ler toda a conversa.

---

## 13. Integração com WhatsApp

A integração planejada será realizada através da **Evolution API**.

Fluxo previsto:

```text
WhatsApp
   ↓
Evolution API
   ↓
FastAPI
   ↓
LangGraph
   ↓
LLM / Tools
   ↓
FastAPI
   ↓
Evolution API
   ↓
WhatsApp
```

Para a POC, poderá ser utilizado o modo de integração baseado em WhatsApp Web.

Essa integração não faz parte da fundação inicial e deverá ser implementada em missão posterior.

A integração deverá permanecer desacoplada da lógica de negócio.

---

## 14. Comunicação entre Containers

O Docker Compose possui inicialmente os serviços:

```text
frontend
backend
postgres
```

Os containers compartilham uma rede criada pelo Docker Compose.

A comunicação interna deverá utilizar os nomes dos serviços.

### Frontend → Backend

```text
frontend
   ↓
http://backend:8000
   ↓
FastAPI
```

### Backend → PostgreSQL

```text
backend
   ↓
postgres:5432
   ↓
PostgreSQL
```

Dentro da rede Docker, `localhost` não deverá ser utilizado para comunicação entre containers diferentes.

`localhost` representa o próprio container.

---

## 15. Configuração

Configurações da aplicação deverão ser fornecidas através de variáveis de ambiente.

Exemplos:

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT
DATABASE_URL
BACKEND_PORT
FRONTEND_PORT
```

O arquivo:

```text
.env.example
```

deverá conter apenas exemplos de configuração.

O arquivo:

```text
.env
```

deverá permanecer fora do controle de versão.

Credenciais reais não deverão ser armazenadas no Git.

---

## 16. Regras Arquiteturais

As seguintes regras deverão ser respeitadas durante o desenvolvimento.

### IA

1. O LLM nunca deverá acessar diretamente o banco de dados.
2. O LLM não deverá inventar dados de imóveis.
3. Dados objetivos sobre imóveis deverão vir da base estruturada.
4. Operações realizadas pelo agente deverão utilizar tools controladas.
5. O cálculo do lead score deverá ser realizado por código.

### Backend

6. Rotas FastAPI não deverão conter regras complexas de negócio.
7. Regras de negócio deverão ficar nos services.
8. Acesso ao banco deverá ficar isolado na camada de persistência.
9. Schemas deverão validar as fronteiras de entrada e saída da API.

### RAG

10. RAG deverá ser utilizado para conhecimento textual.
11. Dados estruturados deverão ser consultados através do PostgreSQL.
12. As fontes utilizadas pelo RAG deverão ser controladas.

### Integrações

13. Integrações externas deverão possuir adaptadores próprios.
14. Código específico de uma integração não deverá ser espalhado pela aplicação.

### Segurança

15. Credenciais não poderão estar no código.
16. Secrets não poderão ser enviados para o Git.
17. Configurações deverão utilizar variáveis de ambiente.
18. Dados sensíveis deverão ser tratados adequadamente.

### Qualidade

19. Toda funcionalidade deverá ser testável.
20. Testes existentes não deverão ser removidos apenas para fazer uma implementação passar.
21. Novas dependências deverão possuir justificativa.
22. Mudanças arquiteturais significativas deverão ser discutidas antes da implementação.

---

## 17. Fluxo Principal do Agente

O fluxo principal planejado será:

```text
Lead inicia conversa
        ↓
Agente identifica intenção
        ↓
Extrai informações já fornecidas
        ↓
Persiste contexto
        ↓
Identifica informações ausentes
        ↓
Realiza perguntas de qualificação
        ↓
Atualiza dados do Lead
        ↓
Calcula Lead Score
        ↓
Busca imóveis compatíveis
        ↓
Apresenta imóveis
        ↓
Lead demonstra interesse
        ↓
Oferece reunião ou visita
        ↓
Realiza agendamento
        ↓
Gera resumo
        ↓
Encaminha para corretor
```

---

## 18. Busca de Imóveis

A busca de imóveis deverá utilizar dados estruturados.

Fluxo:

```text
Conversa
   ↓
LangGraph
   ↓
buscar_imoveis()
   ↓
PropertyService
   ↓
PropertyRepository
   ↓
PostgreSQL
```

Exemplo:

```text
buscar_imoveis(
    cidade="Brasília",
    bairro="Águas Claras",
    tipo="Apartamento",
    preco_max=600000,
    quartos=3
)
```

O retorno deverá conter somente imóveis realmente existentes na base utilizada pela aplicação.

---

## 19. Base de Imóveis

A POC utilizará inicialmente uma base pública de imóveis do Brasil.

O processo planejado será:

```text
CSV
 ↓
Python / Pandas
 ↓
Limpeza
 ↓
Normalização
 ↓
Validação
 ↓
PostgreSQL
```

Os dados deverão ser analisados antes da importação definitiva.

Deverão ser avaliados:

- quantidade de registros;
- colunas disponíveis;
- cobertura geográfica;
- registros duplicados;
- valores ausentes;
- qualidade dos dados;
- adequação aos cenários de compra;
- adequação aos cenários de aluguel;
- adequação aos cenários de investimento.

Caso a base pública não contenha dados suficientes para algum cenário obrigatório da demonstração, poderão ser adicionados dados simulados apenas para complementar os cenários ausentes.

---

## 20. Memória Conversacional

O agente deverá manter o contexto da conversa.

Exemplo:

```text
Usuário:
"Quero um apartamento em Águas Claras."

Agente:
"Qual seria o seu orçamento?"

Usuário:
"Até 600 mil."

Agente:
"Quantos quartos você procura?"

Usuário:
"3."
```

O sistema deverá manter:

```text
regiao = Águas Claras
orcamento_max = 600000
quartos = 3
```

O agente não deverá perguntar novamente essas informações.

A memória deverá combinar:

- histórico necessário da conversa;
- estado estruturado do lead.

Não deverá depender exclusivamente do envio ilimitado de todo o histórico para o LLM.

---

## 21. Observabilidade

A POC deverá possuir observabilidade mínima suficiente para identificar falhas durante a demonstração.

Inicialmente deverão ser considerados:

- logs do backend;
- erros das integrações;
- chamadas relevantes do agente;
- tools utilizadas;
- tempo de resposta;
- falhas de acesso ao banco;
- falhas de comunicação com o LLM.

Logs não deverão expor:

- senhas;
- tokens;
- credenciais;
- informações sensíveis desnecessárias.

---

## 22. Estratégia de Testes

A arquitetura deverá permitir testes em diferentes níveis.

```text
Testes Unitários
       ↓
Testes de Integração
       ↓
Testes de API
       ↓
Testes do Agente
       ↓
Testes E2E
```

### Testes unitários

Utilizados para:

- services;
- lead scoring;
- regras de negócio;
- transformações;
- validações.

### Testes de integração

Utilizados para:

- PostgreSQL;
- repositories;
- pgvector;
- integrações internas.

### Testes de API

Utilizados para validar:

- endpoints;
- status HTTP;
- contratos;
- schemas;
- erros.

### Testes do agente

Deverão validar:

- identificação da intenção;
- extração de informações;
- utilização correta das tools;
- manutenção de contexto;
- ausência de perguntas repetidas;
- comportamento diante de informações ausentes.

### Testes E2E

Deverão validar poucos fluxos críticos completos.

Exemplo:

```text
Lead
 ↓
Conversa
 ↓
Qualificação
 ↓
Busca
 ↓
Recomendação
 ↓
Agendamento
 ↓
Resumo
```

---

## 23. Desenvolvimento Assistido por IA

O projeto poderá utilizar agentes de IA para auxiliar no desenvolvimento.

A abordagem seguirá o conceito de tarefas pequenas e verificáveis.

Fluxo esperado:

```text
Missão
  ↓
Leitura do contexto
  ↓
Leitura das regras
  ↓
Planejamento
  ↓
Implementação
  ↓
Testes
  ↓
Validação
  ↓
Correção
  ↓
Conclusão
```

Antes de realizar alterações, o agente deverá consultar:

```text
AGENTS.md
docs/ARCHITECTURE.md
docs/CONVENTIONS.md
docs/REQUIREMENTS.md
skills/
```

A IA poderá auxiliar na implementação, mas não deverá alterar decisões arquiteturais sem autorização.

---

## 24. Skills

O diretório:

```text
skills/
```

será utilizado para armazenar instruções reutilizáveis para tarefas recorrentes.

Exemplos futuros:

```text
create-fastapi-endpoint.md
create-pytest-test.md
create-service.md
create-repository.md
review-code.md
```

Uma skill deverá definir:

- objetivo;
- contexto necessário;
- regras;
- passos;
- critérios de aceitação;
- validações necessárias.

---

## 25. Guardrails

Os agentes de desenvolvimento deverão respeitar guardrails definidos pelo projeto.

Exemplos:

```text
Não alterar arquitetura sem autorização.

Não adicionar dependências sem necessidade.

Não colocar secrets no código.

Não versionar .env.

Não remover testes para fazer o build passar.

Não inventar dados de imóveis.

Não permitir acesso direto do LLM ao banco.

Não colocar regras de negócio nos controllers/routes.

Não executar operações destrutivas no banco sem autorização.
```

Essas regras deverão ser complementadas pelo `AGENTS.md`.

---

## 26. Definition of Done

Uma funcionalidade somente deverá ser considerada concluída quando:

- implementação estiver concluída;
- requisitos forem atendidos;
- código estiver organizado;
- testes necessários existirem;
- testes estiverem passando;
- aplicação continuar executando;
- não houver regressões conhecidas;
- documentação relevante estiver atualizada;
- critérios de aceitação forem atendidos.

Para tarefas executadas por agentes de IA, o agente deverá apresentar evidências das validações realizadas.

---

## 27. Princípios de Evolução

O projeto seguirá desenvolvimento incremental.

Prioridade:

```text
funcionar
   ↓
testar
   ↓
validar
   ↓
melhorar
```

Não deverão ser implementados componentes apenas porque estão previstos neste documento.

Cada componente deverá ser adicionado quando uma necessidade real da missão exigir sua implementação.

Devemos evitar:

- overengineering;
- abstrações prematuras;
- dependências desnecessárias;
- complexidade sem benefício para a POC.

---

## 28. Evolução Prevista

Evolução planejada:

```text
Fundação
   ↓
Persistência
   ↓
Base de imóveis
   ↓
Busca estruturada
   ↓
LLM local
   ↓
LangGraph
   ↓
Qualificação conversacional
   ↓
Memória
   ↓
RAG
   ↓
Lead Score
   ↓
Follow-up
   ↓
Agendamento
   ↓
Resumo para corretor
   ↓
Dashboard
   ↓
WhatsApp
```

A ordem poderá ser ajustada de acordo com as necessidades do projeto.

---

## 29. Princípio Central da Arquitetura

A inteligência artificial não deverá substituir as regras determinísticas da aplicação.

A arquitetura deverá utilizar cada tecnologia para aquilo em que ela possui maior vantagem.

```text
LLM
│
├── compreender linguagem
├── interpretar intenção
├── extrair informações
├── conduzir conversa
└── gerar respostas naturais


Código
│
├── regras de negócio
├── Lead Score
├── validações
├── permissões
└── controle de fluxo determinístico


PostgreSQL
│
├── leads
├── imóveis
├── conversas
├── agendamentos
└── dados estruturados


RAG + pgvector
│
├── documentos
├── informações de bairros
├── FAQs
├── conhecimento imobiliário
└── conteúdo textual


LangGraph
│
├── estado do agente
├── decisões
├── sequência de execução
├── tools
└── fluxo conversacional
```

O objetivo é utilizar IA onde existe necessidade de interpretação e linguagem, mantendo regras críticas e dados objetivos sob controle determinístico da aplicação.

---

## 30. Resumo da Arquitetura

A arquitetura final planejada pode ser representada como:

```text
                         USUÁRIO
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
             Next.js                WhatsApp
                │                       │
                │                 Evolution API
                │                       │
                └───────────┬───────────┘
                            │
                            ▼
                        FastAPI
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
             Services                LangGraph
                │                       │
                │             ┌─────────┼─────────┐
                │             │         │         │
                │             ▼         ▼         ▼
                │           Tools    llama.cpp    RAG
                │             │         │         │
                │             │         ▼         │
                │             │     Qwen/Gemma    │
                │             │                   │
                └─────────────┼───────────────────┘
                              │
                              ▼
                         PostgreSQL
                              │
                              ▼
                           pgvector
```

Essa arquitetura deverá permitir que a POC demonstre o fluxo completo de um **Agente SDR Imobiliário com IA**, mantendo separação clara entre interface, regras de negócio, inteligência artificial, recuperação de conhecimento, persistência e integrações externas.
