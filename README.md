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

A evolução do projeto poderá combinar essas estratégias:

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

Essa abordagem prepara a aplicação para uma futura estratégia de busca híbrida utilizada pelo agente SDR.

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
```

### Testes adicionados na Missão 05

```text
test_embedding_service.py
test_property_document_service.py
test_property_embedding_repository.py
test_property_embedding_search.py
test_property_semantic_search_api.py
test_property_semantic_search_service.py
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

Após a inclusão dos testes da API semântica, a suíte completa possui:

```text
27 testes
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
│   │   │       └── properties.py
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
│   │   │   └── property.py
│   │   │
│   │   ├── services/
│   │   │   ├── embedding_service.py
│   │   │   ├── property_document_service.py
│   │   │   ├── property_semantic_search_service.py
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
            ┌────────────────┴────────────────┐
            │                                 │
            ▼                                 ▼
 ┌─────────────────────┐          ┌─────────────────────────┐
 │ Consulta estruturada│          │    Busca semântica      │
 │ PropertyService     │          │ SemanticSearchService   │
 └──────────┬──────────┘          └────────────┬────────────┘
            │                                  │
            ▼                                  ▼
 ┌─────────────────────┐          ┌─────────────────────────┐
 │ PropertyRepository  │          │ EmbeddingService        │
 └──────────┬──────────┘          │ multilingual-e5-small   │
            │                     └────────────┬────────────┘
            │                                  │
            │                                  ▼
            │                     ┌─────────────────────────┐
            │                     │ PropertyEmbeddingRepo   │
            │                     └────────────┬────────────┘
            │                                  │
            └──────────────────┬───────────────┘
                               ▼
                    ┌───────────────────────┐
                    │ PostgreSQL + pgvector │
                    │ properties            │
                    │ property_embeddings   │
                    └───────────────────────┘
```

---

## Próximas evoluções

Com a base imobiliária estruturada e a busca semântica implementada, o projeto está preparado para evoluir para as próximas etapas do agente SDR.

Entre as evoluções previstas estão:

- busca híbrida combinando filtros estruturados e similaridade semântica;
- recuperação de contexto imobiliário;
- camada RAG;
- integração com modelo de linguagem local;
- interpretação automática dos requisitos do lead;
- memória/contexto de conversação;
- qualificação de leads;
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
Agente SDR
 │
 ▼
Interpretação da necessidade
 │
 ├───────────────┐
 ▼               ▼
Filtros          Busca semântica
estruturados     pgvector
 │               │
 └───────┬───────┘
         ▼
Imóveis candidatos
         │
         ▼
RAG / contexto
         │
         ▼
LLM
         │
         ▼
Resposta ao lead
```

A Missão 05 estabelece a camada vetorial necessária para que as próximas etapas do agente possam recuperar imóveis utilizando o significado da solicitação do usuário, e não apenas filtros ou correspondências exatas.