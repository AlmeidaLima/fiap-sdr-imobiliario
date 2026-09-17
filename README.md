# Agente SDR Imobiliário com IA

POC desenvolvida para o Hackathon FIAP com o objetivo de criar um agente SDR imobiliário com IA capaz de qualificar leads, manter contexto de conversação, buscar imóveis e apoiar o atendimento comercial.

O projeto utiliza uma arquitetura preparada para evolução para RAG, agentes e integração com canais de atendimento, mantendo componentes locais e open source sempre que possível.

---

## Status do projeto

Projeto em desenvolvimento.

### Missão 01 — Fundação do projeto

**Status: Concluída**

- [x] Repositório criado
- [x] Estrutura de diretórios criada
- [x] FastAPI executando
- [x] Next.js executando
- [x] PostgreSQL executando
- [x] pgvector habilitado
- [x] Docker Compose funcionando
- [x] Endpoint de health funcionando
- [x] Swagger disponível
- [x] Frontend comunicando com backend
- [x] `.env.example` criado
- [x] `.gitignore` criado
- [x] README criado
- [x] ARCHITECTURE criado
- [x] AGENTS criado
- [x] Primeiros testes Pytest executando
- [x] Stack validada em ambiente Docker

---

### Missão 02 — PostgreSQL + pgvector

**Status: Concluída**

- [x] SQLAlchemy 2.x configurado
- [x] psycopg 3 configurado
- [x] Conexão Backend → PostgreSQL validada
- [x] `DATABASE_URL` centralizada
- [x] Engine SQLAlchemy criada
- [x] `SessionLocal` implementada
- [x] `get_db()` implementado
- [x] `Base` declarativa criada
- [x] Teste de conexão com PostgreSQL criado
- [x] Teste de gerenciamento de sessão criado
- [x] pgvector validado pela aplicação
- [x] Inicialização automática do pgvector preparada
- [x] Alembic inicializado e configurado
- [x] Alembic integrado ao `Base.metadata`
- [x] Migration baseline criada e versionada
- [x] Ciclo de migrations validado
- [x] Testes executados dentro do container Docker

#### Persistência

A camada de persistência utiliza:

- SQLAlchemy 2.x
- psycopg 3
- PostgreSQL
- pgvector

A conexão é configurada pela variável:

```text
DATABASE_URL
```

A configuração geral da aplicação está centralizada em:

```text
backend/app/core/config.py
```

O gerenciamento das sessões SQLAlchemy é realizado por:

```text
backend/app/database/session.py
```

A arquitetura básica de persistência é:

```text
FastAPI
   │
   ▼
get_db()
   │
   ▼
SessionLocal
   │
   ▼
SQLAlchemy
   │
   ▼
psycopg
   │
   ▼
PostgreSQL + pgvector
```

#### Migrations

As alterações estruturais do banco são controladas pelo Alembic.

Principais comandos:

```bash
docker compose exec backend alembic current
```

```bash
docker compose exec backend alembic heads
```

```bash
docker compose exec backend alembic upgrade head
```

---

### Missão 03 — API e estrutura

**Status: Concluída**

A Missão 03 estruturou a API FastAPI para permitir o crescimento da aplicação de forma modular.

- [x] Router principal criado
- [x] Endpoints versionados em `/api/v1`
- [x] Endpoint de health padronizado
- [x] Endpoint de informações da aplicação
- [x] Schemas Pydantic separados
- [x] Configuração centralizada
- [x] Tratamento de erros HTTP
- [x] Tratamento de erros da aplicação
- [x] Tratamento de erros de validação
- [x] Contrato padrão de erro
- [x] Testes automatizados dos endpoints
- [x] Regressão executada no Docker

#### Endpoints principais

```text
GET /api/v1/health
GET /api/v1/info
```

O router principal está em:

```text
backend/app/api/router.py
```

As rotas específicas estão em:

```text
backend/app/api/routes/
```

#### Configuração centralizada

As configurações gerais da aplicação são definidas em:

```text
backend/app/core/config.py
```

O objeto `settings` concentra informações como:

```text
app_name
app_description
app_version
database_url
```

#### Tratamento de erros

A aplicação possui handlers centralizados em:

```text
backend/app/core/handlers/
```

São tratados:

```text
HTTPException
ApplicationException
RequestValidationError
```

O contrato de erro é padronizado pela aplicação.

---

### Missão 04 — Modelo e base de imóveis

**Status: Concluída**

A Missão 04 estruturou o domínio de imóveis e importou uma base imobiliária real para utilização pelo agente.

- [x] Dataset imobiliário selecionado
- [x] Dataset analisado
- [x] Modelo `Property` criado
- [x] Campos estruturados e normalizados
- [x] Tabela `properties` criada
- [x] Migrations Alembic criadas
- [x] Repository de imóveis implementado
- [x] Service de imóveis implementado
- [x] Endpoint de consulta de imóveis implementado
- [x] Script de importação criado
- [x] Identificador externo determinístico implementado
- [x] Importação idempotente
- [x] Base importada para PostgreSQL
- [x] Testes de repository implementados
- [x] Testes de service implementados
- [x] Testes da API implementados
- [x] Dataset versionado no projeto
- [x] Origem do dataset documentada

#### Dataset

A base utilizada no projeto é:

```text
Curitiba Apartment Real Estate Data
```

Arquivo:

```text
data/raw/curitiba_apartment_real_estate_data.csv
```

Quantidade importada:

```text
18.760 imóveis
```

#### Origem e atribuição do dataset

O dataset foi obtido no Kaggle:

**Curitiba Apartment Prices**

Autor/publicador:

```text
wittmannf
```

A base é utilizada neste projeto exclusivamente como fonte de dados para fins acadêmicos, experimentação e desenvolvimento do POC do Hackathon FIAP.

O projeto mantém a atribuição da origem do dataset e sua utilização deve respeitar os termos e a licença informados pelo publicador da base.

#### Modelo Property

O domínio imobiliário possui informações como:

```text
external_id
title
description
usable_area
total_area
bedrooms
suites
bathrooms
parking_spaces
street
zip_code
neighborhood
price
monthly_condo_fee
yearly_iptu
amenities
pois
source
available
```

O campo:

```text
external_id
```

é utilizado como identificador externo determinístico, permitindo que a importação seja executada de forma idempotente.

#### Consulta de imóveis

Endpoint:

```text
GET /api/v1/properties
```

A consulta permite utilizar filtros estruturados sobre os imóveis armazenados no PostgreSQL.

---

### Missão 05 — Embeddings e busca semântica

**Status: Concluída**

A Missão 05 adicionou a primeira camada de recuperação semântica do projeto.

Os imóveis armazenados no PostgreSQL são transformados em documentos textuais normalizados, convertidos em embeddings e persistidos utilizando `pgvector`.

Isso permite que o agente pesquise imóveis utilizando linguagem natural, sem depender apenas de correspondências exatas de campos ou palavras.

#### Definition of Done

- [x] Modelo de embeddings definido
- [x] Modelo executado localmente
- [x] Dependência de API externa não necessária para embeddings
- [x] `sentence-transformers` integrado ao backend
- [x] Dimensão dos embeddings definida
- [x] Tabela `property_embeddings` criada
- [x] Migration Alembic criada
- [x] Integração com pgvector validada
- [x] Model `PropertyEmbedding` criado
- [x] `EmbeddingService` implementado
- [x] Embedding de documentos implementado
- [x] Embedding de consultas implementado
- [x] `PropertyDocumentService` implementado
- [x] Dados estruturados incorporados ao documento
- [x] Amenities normalizadas
- [x] POIs normalizados
- [x] HTML removido antes da geração dos embeddings
- [x] Espaços e textos normalizados
- [x] Limite de tamanho do documento definido
- [x] `PropertyEmbeddingRepository` implementado
- [x] Persistência vetorial implementada
- [x] Busca por similaridade implementada
- [x] `similarity_score` implementado
- [x] `PropertySemanticSearchService` implementado
- [x] Endpoint de busca semântica implementado
- [x] Consulta em linguagem natural implementada
- [x] Parâmetro `limit` implementado
- [x] Script de indexação implementado
- [x] Indexação idempotente
- [x] Processamento em lotes
- [x] Recuperação após interrupção
- [x] Tratamento de erros durante a indexação
- [x] Base completa indexada
- [x] 18.760 imóveis com embeddings
- [x] 0 imóveis disponíveis pendentes
- [x] 0 embeddings duplicados
- [x] 0 erros na indexação completa
- [x] Busca semântica validada com a base completa
- [x] Testes automatizados do serviço de embeddings
- [x] Testes automatizados da construção dos documentos
- [x] Testes automatizados do repository
- [x] Teste de integração da similaridade vetorial
- [x] Testes automatizados do serviço de busca semântica
- [x] Testes automatizados do endpoint semântico
- [x] Regressão completa do backend validada

---

### Missão 06 — Busca híbrida de imóveis

**Status: Concluída**

A Missão 06 evoluiu a recuperação de imóveis combinando a busca semântica da Missão 05 com filtros estruturados determinísticos.

A estratégia permite utilizar linguagem natural para representar preferências subjetivas do lead, mantendo restrições objetivas como bairro, preço, quartos e área útil como filtros obrigatórios.

#### Definition of Done

- [x] Busca semântica da Missão 05 reutilizada
- [x] `PropertyEmbeddingRepository` evoluído para busca com filtros estruturados
- [x] Filtro por bairro
- [x] Filtro por preço mínimo
- [x] Filtro por preço máximo
- [x] Filtro por quantidade mínima de quartos
- [x] Filtro por quantidade mínima de banheiros
- [x] Filtro por quantidade mínima de vagas
- [x] Filtro por área útil mínima
- [x] Filtro por disponibilidade
- [x] Ranking por similaridade vetorial preservado
- [x] `PropertyHybridSearchService` implementado
- [x] Schema `PropertySearchResponse` implementado
- [x] Endpoint `GET /api/v1/properties/hybrid-search` implementado
- [x] Parâmetro `q` obrigatório e validado
- [x] Parâmetro `limit` validado entre 1 e 20
- [x] Validações de filtros numéricos implementadas
- [x] Handler de validação ajustado para serialização de valores como `Decimal`
- [x] Teste do repository da busca híbrida
- [x] Teste do service da busca híbrida
- [x] Testes da API da busca híbrida
- [x] Busca híbrida validada contra a base real
- [x] Filtros objetivos validados em conjunto com o ranking semântico
- [x] Alteração da consulta textual validada com mudança do ranking
- [x] Base com 18.760 imóveis e 18.760 embeddings disponível para consulta
- [x] Regressão completa executada
- [x] 34 testes automatizados passando

#### Endpoint de busca híbrida

```text
GET /api/v1/properties/hybrid-search
```

Exemplo conceitual:

```text
GET /api/v1/properties/hybrid-search?q=apartamento para família com academia e churrasqueira&neighborhood=Boa Vista&max_price=700000&min_bedrooms=3&min_usable_area=70&limit=5
```

A consulta combina dois tipos de critérios:

```text
Preferências semânticas             Restrições estruturadas
"para família"                     bairro = Boa Vista
"academia"                         preço <= 700000
"churrasqueira"                    quartos >= 3
                                    área útil >= 70 m²
```

Somente imóveis que atendem aos filtros estruturados participam do resultado, e esses candidatos são ordenados por similaridade semântica.

#### Validação com a base real

A primeira consulta validada foi:

```text
apartamento para família com academia e churrasqueira
```

com os filtros:

```text
Bairro: Boa Vista
Preço máximo: R$ 700.000
Quartos: mínimo 3
Área útil: mínimo 70 m²
```

Top 5 obtido:

```text
4397
5703
4270
850
440
```

Mantendo os mesmos filtros e alterando somente a consulta para:

```text
apartamento tranquilo próximo a transporte público
```

o Top 5 passou a ser:

```text
4397
6611
2302
7094
8997
```

Quatro dos cinco imóveis do Top 5 foram alterados, enquanto os filtros estruturados continuaram sendo respeitados. Isso evidencia que a intenção textual influencia o ranking semântico sem flexibilizar as restrições objetivas.

#### Arquitetura da busca híbrida

```text
Consulta do lead
      │
      ├── linguagem natural ──> EmbeddingService
      │                              │
      │                              ▼
      │                        vetor da consulta
      │
      └── filtros objetivos ──> filtros SQL/SQLAlchemy
                                     │
                    ┌────────────────┘
                    ▼
          PropertyHybridSearchService
                    │
                    ▼
        PropertyEmbeddingRepository
                    │
                    ▼
           PostgreSQL + pgvector
                    │
                    ▼
        candidatos que cumprem filtros
                    │
                    ▼
          ranking por similaridade
```

---

### Missão 07 — Interpretação da intenção e busca em linguagem natural

**Status: Concluída**

A Missão 07 adicionou uma camada de interpretação determinística da mensagem do lead. Agora o consumidor pode enviar uma frase em linguagem natural, e o backend extrai automaticamente os critérios estruturados antes de delegar a recuperação para a busca híbrida da Missão 06.

A implementação atual utiliza regras e expressões regulares, mantendo a interpretação desacoplada da busca. Isso prepara a arquitetura para substituir ou complementar o parser por um LLM no futuro sem alterar a camada de recuperação imobiliária.

#### Definition of Done

- [x] Schema `PropertySearchIntent` implementado
- [x] Contrato HTTP `PropertyNaturalLanguageSearchRequest` implementado
- [x] Campos não informados tratados como `None`
- [x] Validação de valores por Pydantic
- [x] `PropertySearchIntentService` implementado
- [x] Normalização básica da mensagem
- [x] Extração de bairro
- [x] Extração de preço máximo
- [x] Suporte a preço no formato `700 mil`
- [x] Suporte a preço no formato `R$ 650.000`
- [x] Extração de quantidade mínima de quartos
- [x] Extração de quantidade mínima de banheiros
- [x] Extração de quantidade mínima de vagas
- [x] Extração de área útil mínima
- [x] Preferências subjetivas preservadas em `semantic_query`
- [x] `PropertyNaturalLanguageSearchService` implementado
- [x] Integração entre interpretação da intenção e `PropertyHybridSearchService`
- [x] Endpoint `POST /api/v1/properties/natural-language-search` implementado
- [x] `message` obrigatório e com tamanho mínimo validado
- [x] `limit` validado entre 1 e 20
- [x] `limit=5` utilizado como padrão
- [x] Testes automatizados do schema de intenção
- [x] Testes automatizados do interpretador
- [x] Teste da orquestração entre intenção e busca híbrida
- [x] Testes automatizados do endpoint de linguagem natural
- [x] Teste ponta a ponta executado contra a base real
- [x] Extração do parser validada diretamente
- [x] Base com 18.760 imóveis e 18.760 embeddings utilizada na validação
- [x] Regressão completa executada
- [x] 48 testes automatizados passando

#### Endpoint de busca em linguagem natural

```text
POST /api/v1/properties/natural-language-search
```

Exemplo de requisição:

```json
{
  "message": "Quero um apartamento no Boa Vista com 3 quartos, pelo menos 70 m², até 700 mil. Gostaria de academia e churrasqueira.",
  "limit": 5
}
```

O parser transforma a mensagem em uma intenção estruturada equivalente a:

```text
neighborhood        = Boa Vista
max_price           = 700000
min_bedrooms        = 3
min_usable_area     = 70
min_price           = null
min_bathrooms       = null
min_parking_spaces  = null
semantic_query      = mensagem do lead
```

#### Validação ponta a ponta

A mensagem acima retornou cinco imóveis reais, todos respeitando simultaneamente os filtros extraídos:

```text
ID     Bairro       Preço       Quartos   Área    Similaridade
8774   Boa Vista    279.990       3        73       0,8820
5703   Boa Vista    671.955       3        85       0,8730
4919   Boa Vista    575.910       3        88       0,8700
7094   Boa Vista    475.900       3        71       0,8700
545    Boa Vista    699.000       3        87       0,8696
```

O teste comprovou o fluxo completo:

```text
Mensagem do lead
        │
        ▼
PropertySearchIntentService
        │
        ▼
PropertySearchIntent
        │
        ├── filtros objetivos
        │   bairro / preço / quartos / área
        │
        └── semantic_query
                 │
                 ▼
PropertyNaturalLanguageSearchService
                 │
                 ▼
PropertyHybridSearchService
                 │
        ┌────────┴────────┐
        ▼                 ▼
   filtros SQL        embedding
        │                 │
        └────────┬────────┘
                 ▼
       PostgreSQL + pgvector
                 │
                 ▼
          imóveis relevantes
```

---

### Missão 08 — Estado de conversa e qualificação mínima do lead

**Status: Concluída**

A Missão 08 adicionou continuidade conversacional ao backend. O agente passa a acumular os critérios informados pelo lead ao longo de vários turnos, preservar informações anteriores, substituir critérios alterados e identificar quais dados ainda faltam para iniciar a busca de imóveis.

Nesta etapa, a qualificação é determinística e representa a **qualificação mínima para busca de imóveis**. A conversa é considerada pronta para busca quando possui bairro, preço máximo e quantidade mínima de quartos. A qualificação comercial completa do SDR, incluindo intenção de compra/aluguel/investimento, urgência, lead score e persistência do lead, permanece como evolução posterior.

#### Definition of Done

- [x] `ConversationState` implementado
- [x] Identificação da conversa por `conversation_id`
- [x] Estado acumulado entre múltiplos turnos
- [x] Preservação dos critérios informados anteriormente
- [x] Sobrescrita de critérios quando o lead altera uma preferência
- [x] Acúmulo de preferências semânticas
- [x] Integração com `PropertySearchIntentService`
- [x] Proteção para não interpretar a expressão `na verdade` como bairro
- [x] `ConversationQualificationService` implementado
- [x] Identificação dos campos obrigatórios ainda ausentes
- [x] Geração determinística da próxima pergunta
- [x] Busca de imóveis bloqueada enquanto a conversa não estiver qualificada
- [x] `ConversationPropertySearchService` implementado
- [x] Integração da conversa qualificada com `PropertyHybridSearchService`
- [x] Endpoint `POST /api/v1/conversations/turn` implementado
- [x] Testes unitários de estado, merge, fluxo e qualificação
- [x] Testes da integração conversa → busca híbrida
- [x] Teste de API em múltiplos turnos
- [x] Teste ponta a ponta utilizando PostgreSQL + pgvector e a base real
- [x] Validação dos imóveis retornados contra bairro, preço e quartos acumulados
- [x] Regressão completa executada
- [x] 69 testes automatizados passando

#### Endpoint conversacional

```text
POST /api/v1/conversations/turn
```

Exemplo de evolução da conversa:

```text
Turno 1
Lead: Quero um apartamento no Boa Vista

Estado:
neighborhood = Boa Vista
max_price = null
min_bedrooms = null

Próxima pergunta:
Qual é o valor máximo que você pretende investir no imóvel?

Turno 2
Lead: Até 700 mil

Estado acumulado:
neighborhood = Boa Vista
max_price = 700000
min_bedrooms = null

Próxima pergunta:
Quantos quartos você procura?

Turno 3
Lead: Quero pelo menos 3 quartos

Estado acumulado:
neighborhood = Boa Vista
max_price = 700000
min_bedrooms = 3
qualified = true
```

Quando a qualificação mínima é atingida, o fluxo executa a busca híbrida e retorna imóveis compatíveis com os critérios acumulados.

#### Fluxo implementado

```text
Mensagem do lead
       │
       ▼
PropertySearchIntentService
       │
       ▼
ConversationService
       │
       ├── atualiza ConversationState
       │
       ▼
ConversationQualificationService
       │
       ├── não qualificado ──> próxima pergunta
       │
       └── qualificado
              │
              ▼
ConversationPropertySearchService
              │
              ▼
PropertyHybridSearchService
              │
       ┌──────┴──────┐
       ▼             ▼
 filtros SQL      embedding
       │             │
       └──────┬──────┘
              ▼
     PostgreSQL + pgvector
              │
              ▼
       imóveis compatíveis
```

#### Estado conversacional atual

O estado suporta os seguintes critérios:

```text
conversation_id
neighborhood
min_price
max_price
min_bedrooms
min_bathrooms
min_parking_spaces
min_usable_area
semantic_preferences
```

Nesta versão, o estado é devolvido pela API e reenviado pelo cliente no turno seguinte. A persistência e recuperação automática do estado por `conversation_id` ainda não fazem parte desta missão.


## Modelo de embeddings

O modelo selecionado para geração dos embeddings foi:

```text
intfloat/multilingual-e5-small
```

O modelo é carregado através da biblioteca:

```text
sentence-transformers
```

A geração dos embeddings ocorre localmente, sem necessidade de utilizar uma API externa de IA.

### Dimensão

Cada imóvel é representado por um vetor de:

```text
384 dimensões
```

Esses vetores são armazenados no PostgreSQL utilizando:

```text
pgvector
```

Arquitetura:

```text
Property
   │
   ▼
PropertyDocumentService
   │
   ▼
Documento normalizado
   │
   ▼
EmbeddingService
   │
   ▼
multilingual-e5-small
   │
   ▼
Vector(384)
   │
   ▼
PostgreSQL + pgvector
```

---

## Construção do documento semântico

Antes da geração do embedding, cada imóvel é transformado em um documento textual pelo:

```text
PropertyDocumentService
```

O documento pode incorporar informações como:

```text
Título
Bairro
Rua
CEP
Área útil
Área total
Quartos
Suítes
Banheiros
Vagas
Preço
Condomínio
IPTU
Comodidades
Pontos de interesse
Descrição
```

Exemplo conceitual:

```text
Título: Apartamento no Boa Vista.
Bairro: Boa Vista.
Área útil: 77 m².
Quartos: 3.
Suítes: 1.
Banheiros: 2.
Vagas: 1.
Preço: R$ 595000.
Comodidades: churrasqueira, academia, aceita pets.
Pontos de interesse: ponto de ônibus, farmácia.
Descrição: Apartamento ensolarado e bem localizado.
```

### Normalização

Antes da vetorização são realizadas operações como:

- conversão de entidades HTML;
- remoção de `<br>`;
- remoção de outras tags HTML;
- normalização de espaços;
- normalização de amenities;
- normalização dos pontos de interesse;
- limitação do documento.

O limite atual é:

```text
MAX_DOCUMENT_LENGTH = 4000
```

O conteúdo original da propriedade permanece preservado na tabela `properties`.

A limpeza é aplicada ao documento utilizado para geração do embedding.

---

## Amenities

As amenities do dataset são convertidas para termos mais adequados à busca em português.

Exemplos:

```text
BARBECUE_GRILL     → churrasqueira
GYM                → academia
POOL               → piscina
PARTY_HALL         → salão de festas
GOURMET_SPACE      → espaço gourmet
GOURMET_BALCONY    → varanda gourmet
PETS_ALLOWED       → aceita pets
SPORTS_COURT       → quadra esportiva
PLAYGROUND         → playground
CONCIERGE_24H      → portaria 24 horas
AIR_CONDITIONING   → ar-condicionado
```

Essa normalização melhora o conteúdo utilizado pelo modelo de embeddings.

---

## Pontos de interesse

Os POIs também são incorporados ao documento semântico.

Exemplos de categorias:

```text
BS → ponto de ônibus
TS → transporte
CS → comércio
PH → farmácia
CH → saúde
VP → pet shop ou veterinário
```

Isso permite consultas como:

```text
apartamento próximo a transporte público
```

mesmo quando a informação relevante está nos pontos de interesse e não diretamente no título do anúncio.

---

## Persistência dos embeddings

Os embeddings são armazenados na tabela:

```text
property_embeddings
```

Cada registro mantém a associação com um imóvel através de:

```text
property_id
```

e armazena informações como:

```text
content
embedding
embedding_model
```

A dimensão esperada do vetor é:

```text
384
```

---

## Indexação dos imóveis

O script responsável pela indexação está em:

```text
backend/scripts/index_property_embeddings.py
```

A indexação é:

```text
idempotente
```

Imóveis que já possuem embedding não são processados novamente.

O script também trabalha em lotes, permitindo controlar a quantidade processada por transação.

Exemplo:

```bash
docker compose exec backend python -m scripts.index_property_embeddings --batch-size 100
```

Para limitar a quantidade:

```bash
docker compose exec backend python -m scripts.index_property_embeddings --limit 100 --batch-size 50
```

Caso o processo seja interrompido, o mesmo comando pode ser executado novamente.

O script continuará somente com imóveis ainda sem embedding.

### Resultado da indexação completa

A base foi indexada com:

```text
Properties:             18.760
Property embeddings:    18.760
Cobertura:               100%
Pendentes:               0
Duplicidades:            0
Erros na indexação:      0
Dimensão:                384
```

Modelo:

```text
intfloat/multilingual-e5-small
```

---

## Busca semântica

Endpoint:

```text
GET /api/v1/properties/semantic-search
```

Parâmetros:

```text
q
limit
```

`q` representa a consulta em linguagem natural.

`limit` define a quantidade máxima de resultados retornados.

Exemplo:

```text
GET /api/v1/properties/semantic-search?q=apartamento com academia e churrasqueira&limit=5
```

A resposta contém os dados do imóvel e:

```text
similarity_score
```

Exemplo simplificado:

```json
[
  {
    "id": 4435,
    "external_id": "...",
    "title": "...",
    "neighborhood": "Pinheirinho",
    "usable_area": 0,
    "bedrooms": 0,
    "bathrooms": 0,
    "parking_spaces": 0,
    "price": 0,
    "similarity_score": 0.8866
  }
]
```

Os valores do exemplo são apenas ilustrativos, com exceção do identificador, bairro e score registrados durante a validação.

---

## Validação da busca semântica

A busca foi validada inicialmente com uma amostra reduzida e posteriormente contra os:

```text
18.760 embeddings
```

### Academia e churrasqueira

Consulta:

```text
apartamento com academia e churrasqueira
```

Exemplos encontrados entre os primeiros resultados:

```text
ID 4435 — Pinheirinho
similarity_score: 0.8866
academia + churrasqueira

ID 1474 — São Lourenço
similarity_score: 0.8838
churrasqueira + gourmet

ID 5062 — Atuba
similarity_score: 0.8810
academia + gourmet

ID 3115 — Cabral
similarity_score: 0.8800
academia + churrasqueira

ID 5585 — Pinheirinho
similarity_score: 0.8799
churrasqueira
```

### Transporte público

Também foi validada a consulta:

```text
apartamento próximo a transporte público
```

A relevância pode ser encontrada tanto na descrição quanto nos POIs incorporados ao documento utilizado para gerar o embedding.

### Família e área de lazer

Consulta validada:

```text
apartamento para família com 3 quartos e área de lazer
```

### Piscina e academia

Consulta validada:

```text
apartamento com piscina e academia
```

O endpoint retornou os resultados esperados contra a base completa.

---

## Busca semântica e filtros determinísticos

A validação da Missão 05 demonstrou uma separação arquitetural importante.

Características objetivas são melhores candidatas a filtros estruturados:

```text
bairro
preço máximo
preço mínimo
quantidade de quartos
quantidade de banheiros
quantidade de vagas
área mínima
```

Preferências ou intenções podem utilizar busca semântica:

```text
bom para família
perto de transporte
boa área de lazer
apartamento confortável
condomínio com estrutura
próximo a comércio
```

A Missão 06 passou a combinar essas estratégias por meio da busca híbrida:

```text
Consulta do usuário
        │
        ▼
Interpretação da intenção
        │
        ├───────────────┐
        ▼               ▼
Filtros estruturados   Busca semântica
        │               │
        └───────┬───────┘
                ▼
           Ranking final
```

Essa abordagem foi implementada na Missão 06 por meio do endpoint de busca híbrida, preservando filtros determinísticos e utilizando similaridade vetorial para o ranking final.

---

## Testes automatizados

Os testes do backend são executados com:

```bash
docker compose exec backend python -m pytest -v
```

A suíte cobre:

```text
conexão com PostgreSQL
gerenciamento de sessão
pgvector
healthcheck
informações da aplicação
tratamento de erros
validação de schemas
consulta estruturada de imóveis
PropertyRepository
PropertyService
EmbeddingService
PropertyDocumentService
PropertyEmbeddingRepository
busca vetorial real
PropertySemanticSearchService
endpoint de busca semântica
busca híbrida
PropertyHybridSearchService
endpoint de busca híbrida
interpretação estruturada da intenção do lead
PropertySearchIntentService
PropertyNaturalLanguageSearchService
endpoint de busca em linguagem natural
```

### Testes adicionados nas Missões 05, 06 e 07

```text
test_embedding_service.py
test_property_document_service.py
test_property_embedding_repository.py
test_property_embedding_search.py
test_property_semantic_search_api.py
test_property_semantic_search_service.py
test_property_hybrid_search_repository.py
test_property_hybrid_search_service.py
test_property_hybrid_search_api.py
test_property_search_intent.py
test_property_search_intent_service.py
test_property_natural_language_search_service.py
test_property_natural_language_search_api.py
```

O teste específico da API semântica valida:

```text
q obrigatório
tamanho mínimo da consulta
HTTP 200 em consulta válida
estrutura da resposta
similarity_score
limit
limite máximo permitido
```

Após a conclusão da Missão 08, a suíte completa possui:

```text
69 testes
```

A regressão final da missão deve permanecer integralmente verde antes do fechamento do commit.

Avisos de depreciação de dependências podem aparecer durante a execução do Pytest e são tratados como dívida técnica, não como falha funcional da missão.

---

## Stack

Tecnologias utilizadas atualmente:

- Python 3.12
- FastAPI
- SQLAlchemy 2.x
- psycopg 3
- Alembic
- Pydantic
- React
- Next.js
- PostgreSQL
- pgvector
- pandas
- sentence-transformers
- PyTorch
- Docker
- Docker Compose
- Pytest

Modelo de embeddings:

```text
intfloat/multilingual-e5-small
```

Tecnologias planejadas para evolução do projeto:

- LangGraph
- llama.cpp
- Modelo local Qwen ou Gemma
- RAG
- Evolution API

---

## Estrutura do projeto

```text
fiap-sdr-imobiliario/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   │       ├── 64bbb5ca46ba_...
│   │       ├── 88433f05b0e8_create_properties_table.py
│   │       ├── ba7235f16efa_add_property_external_id.py
│   │       ├── 76bc84d41477_make_property_external_id_required.py
│   │       └── 07605d3cb9a0_create_property_embeddings_table.py
│   │
│   ├── app/
│   │   ├── agents/
│   │   │
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   └── routes/
│   │   │       ├── health.py
│   │   │       ├── info.py
│   │   │       ├── properties.py
│   │   │       └── conversations.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── exceptions.py
│   │   │   └── handlers/
│   │   │       ├── application_exception.py
│   │   │       ├── http_exception.py
│   │   │       └── validation_exception.py
│   │   │
│   │   ├── database/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   ├── property_repository.py
│   │   │   └── property_embedding_repository.py
│   │   │
│   │   ├── integrations/
│   │   │
│   │   ├── models/
│   │   │   ├── property.py
│   │   │   └── property_embedding.py
│   │   │
│   │   ├── rag/
│   │   │
│   │   ├── schemas/
│   │   │   ├── error.py
│   │   │   ├── health.py
│   │   │   ├── info.py
│   │   │   ├── property.py
│   │   │   ├── property_search_intent.py
│   │   │   └── conversation.py
│   │   │
│   │   ├── services/
│   │   │   ├── embedding_service.py
│   │   │   ├── property_document_service.py
│   │   │   ├── property_semantic_search_service.py
│   │   │   ├── property_hybrid_search_service.py
│   │   │   ├── property_search_intent_service.py
│   │   │   ├── property_natural_language_search_service.py
│   │   │   ├── conversation_service.py
│   │   │   ├── conversation_qualification_service.py
│   │   │   ├── conversation_property_search_service.py
│   │   │   └── property_service.py
│   │   │
│   │   └── tools/
│   │
│   ├── scripts/
│   │   ├── __init__.py
│   │   ├── import_curitiba_properties.py
│   │   └── index_property_embeddings.py
│   │
│   ├── tests/
│   │   ├── test_database_connection.py
│   │   ├── test_database_session.py
│   │   ├── test_embedding_service.py
│   │   ├── test_error_handler.py
│   │   ├── test_error_schema.py
│   │   ├── test_health.py
│   │   ├── test_info.py
│   │   ├── test_pgvector.py
│   │   ├── test_properties_api.py
│   │   ├── test_property_document_service.py
│   │   ├── test_property_embedding_repository.py
│   │   ├── test_property_embedding_search.py
│   │   ├── test_property_repository.py
│   │   ├── test_property_semantic_search_api.py
│   │   ├── test_property_semantic_search_service.py
│   │   ├── test_property_hybrid_search_repository.py
│   │   ├── test_property_hybrid_search_service.py
│   │   ├── test_property_hybrid_search_api.py
│   │   ├── test_property_search_intent.py
│   │   ├── test_property_search_intent_service.py
│   │   ├── test_property_natural_language_search_service.py
│   │   ├── test_property_natural_language_search_api.py
│   │   ├── test_conversation_state.py
│   │   ├── test_conversation_service.py
│   │   ├── test_conversation_flow.py
│   │   ├── test_conversation_qualification_service.py
│   │   ├── test_conversation_turn.py
│   │   ├── test_conversation_property_search_service.py
│   │   ├── test_conversation_search_flow.py
│   │   ├── test_conversation_api.py
│   │   ├── test_property_service.py
│   │   └── test_validation_handler.py
│   │
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   ├── public/
│   ├── Dockerfile
│   └── package.json
│
├── data/
│   ├── knowledge/
│   ├── processed/
│   └── raw/
│       └── curitiba_apartment_real_estate_data.csv
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONVENTIONS.md
│   └── REQUIREMENTS.md
│
├── scripts/
│   └── postgres/
│       └── init.sql
│
├── skills/
├── .env.example
├── .gitignore
├── AGENTS.md
├── compose.yaml
└── README.md
```

---

## Como executar o projeto

### Pré-requisitos

Para executar o projeto é necessário possuir:

- Git
- Docker
- Docker Compose

Não é necessário instalar Python, PostgreSQL ou Node.js localmente para executar a aplicação através do Docker.

---

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd fiap-sdr-imobiliario
```

---

### 2. Criar o arquivo de configuração

O projeto disponibiliza:

```text
.env.example
```

Crie uma cópia chamada:

```text
.env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

O arquivo `.env` não deve ser versionado.

---

### 3. Subir os containers

```bash
docker compose up --build
```

Ou em segundo plano:

```bash
docker compose up -d --build
```

---

### 4. Verificar os containers

```bash
docker compose ps
```

---

### 5. Executar as migrations

```bash
docker compose exec backend alembic upgrade head
```

Para verificar a migration atual:

```bash
docker compose exec backend alembic current
```

---

### 6. Importar os imóveis

A base pode ser importada através do script de importação do backend.

```bash
docker compose exec backend python -m scripts.import_curitiba_properties
```

A importação utiliza identificadores externos determinísticos para evitar duplicações.

---

### 7. Gerar os embeddings

Para indexar todos os imóveis ainda não indexados:

```bash
docker compose exec backend python -m scripts.index_property_embeddings --batch-size 100
```

Para executar uma amostra:

```bash
docker compose exec backend python -m scripts.index_property_embeddings --limit 100 --batch-size 50
```

---

### 8. Validar o backend

Healthcheck:

```text
GET /api/v1/health
```

Swagger:

```text
/docs
```

Informações da aplicação:

```text
GET /api/v1/info
```

Consulta estruturada:

```text
GET /api/v1/properties
```

Busca semântica:

```text
GET /api/v1/properties/semantic-search
```

Busca híbrida:

```text
GET /api/v1/properties/hybrid-search
```

---

### 9. Executar os testes

```bash
docker compose exec backend python -m pytest -v
```

---

## Arquitetura atual

```text
                         ┌───────────────────┐
                         │     Frontend      │
                         │      Next.js      │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │      FastAPI      │
                         │    /api/v1/*      │
                         └─────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
       Busca estruturada     Busca híbrida       Linguagem natural
       PropertyService    HybridSearchService    IntentService
              │                    │                    │
              │                    │                    ▼
              │                    │       PropertySearchIntent
              │                    │                    │
              │                    │                    ▼
              │                    │     NaturalLanguageSearchService
              │                    │                    │
              │                    ◄────────────────────┘
              │                    │
              ▼                    ▼
     PropertyRepository    EmbeddingService
                                   │
                                   ▼
                       PropertyEmbeddingRepository
                                   │
                         ┌─────────┴─────────┐
                         ▼                   ▼
                    filtros SQL      similaridade vetorial
                         │                   │
                         └─────────┬─────────┘
                                   ▼
                         PostgreSQL + pgvector
```

---

## Próximas evoluções

Com a base imobiliária estruturada, a busca híbrida e a interpretação determinística da intenção implementadas, o projeto está preparado para evoluir para as próximas etapas do agente SDR.

Entre as evoluções previstas estão:

- recuperação de contexto imobiliário;
- camada RAG;
- integração com modelo de linguagem local;
- persistência do estado conversacional por `conversation_id`;
- qualificação comercial completa de leads e lead score;
- orquestração do agente;
- integração com canais de atendimento;
- guardrails;
- observabilidade e avaliação das respostas.

---

## Objetivo arquitetural

A evolução esperada do projeto é:

```text
Lead
 │
 ▼
Mensagem em linguagem natural
 │
 ▼
Interpretação da necessidade
 │
 ├───────────────┐
 ▼               ▼
Filtros          Preferências semânticas
estruturados     / embedding
 │               │
 └───────┬───────┘
         ▼
Busca híbrida
PostgreSQL + pgvector
         │
         ▼
Imóveis candidatos
         │
         ▼
RAG / contexto
         │
         ▼
LLM / Agente SDR
         │
         ▼
Resposta ao lead
```

As Missões 05, 06 e 07 estabelecem a camada de recuperação e interpretação inicial do agente. A Missão 05 adiciona a representação vetorial e a busca por significado; a Missão 06 combina similaridade com filtros estruturados; e a Missão 07 permite que uma mensagem natural do lead seja convertida automaticamente em uma intenção tipada e encaminhada à busca híbrida.

A interpretação da Missão 07 é atualmente determinística, baseada em regras e expressões regulares. A arquitetura mantém essa responsabilidade desacoplada para permitir futura integração com um LLM sem alterar a camada de recuperação de imóveis.

A Missão 08 acrescenta a camada de estado e decisão conversacional: os critérios podem ser coletados em vários turnos, a aplicação identifica o que ainda falta e somente aciona a recuperação imobiliária quando existe informação mínima suficiente para a busca.
