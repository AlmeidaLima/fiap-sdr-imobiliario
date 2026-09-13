# 🏠 Agente SDR Imobiliário com IA

Projeto desenvolvido como parte do Hackathon da Pós-Graduação **IA para Devs — FIAP**.

O objetivo do projeto é desenvolver um **Agente SDR Imobiliário com Inteligência Artificial**, capaz de apoiar a prospecção e qualificação de potenciais clientes interessados em imóveis.

A solução será capaz de consultar uma base real de imóveis, identificar propriedades compatíveis com as necessidades do cliente e utilizar técnicas de Inteligência Artificial e RAG para fornecer recomendações contextualizadas.

---

# 🎯 Objetivo

Construir um agente SDR imobiliário capaz de:

- Interagir com potenciais clientes;
- Identificar preferências e necessidades;
- Consultar uma base real de imóveis;
- Filtrar imóveis por características relevantes;
- Utilizar busca semântica;
- Utilizar RAG (Retrieval-Augmented Generation);
- Recomendar imóveis compatíveis com o perfil do cliente;
- Manter uma arquitetura modular e evolutiva;
- Permitir execução local por todos os integrantes do projeto.

---

# 🏗️ Arquitetura

A aplicação está organizada inicialmente nos seguintes componentes:

```text
Frontend
   │
   ▼
Next.js
   │
   ▼
FastAPI
   │
   ├── API REST
   ├── Services
   ├── Repositories
   ├── ETL
   │
   ▼
PostgreSQL
   │
   └── pgvector
```

Tecnologias principais:

| Tecnologia | Utilização |
|---|---|
| Python | Backend e processamento de dados |
| FastAPI | API REST |
| Pydantic | Validação e schemas |
| SQLAlchemy | ORM e persistência |
| Alembic | Migrations |
| PostgreSQL | Banco de dados |
| pgvector | Armazenamento/busca vetorial |
| Pandas | Processamento do dataset |
| Pytest | Testes automatizados |
| Next.js | Frontend |
| Docker | Containerização |
| Docker Compose | Orquestração local |
| Git / GitHub | Versionamento e colaboração |

---

# 📁 Estrutura do projeto

```text
fiap-sdr-imobiliario/
│
├── backend/
│   │
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── health.py
│   │   │   │   ├── info.py
│   │   │   │   └── properties.py
│   │   │   └── router.py
│   │   │
│   │   ├── core/
│   │   │   ├── handlers/
│   │   │   ├── config.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── database/
│   │   │   ├── base.py
│   │   │   ├── property_repository.py
│   │   │   └── session.py
│   │   │
│   │   ├── models/
│   │   │   └── property.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── error.py
│   │   │   ├── health.py
│   │   │   ├── info.py
│   │   │   └── property.py
│   │   │
│   │   ├── services/
│   │   │   └── property_service.py
│   │   │
│   │   └── main.py
│   │
│   ├── scripts/
│   │   ├── __init__.py
│   │   └── import_curitiba_properties.py
│   │
│   ├── tests/
│   │   ├── test_database_connection.py
│   │   ├── test_database_session.py
│   │   ├── test_error_handler.py
│   │   ├── test_error_schema.py
│   │   ├── test_health.py
│   │   ├── test_info.py
│   │   ├── test_pgvector.py
│   │   ├── test_properties_api.py
│   │   ├── test_property_repository.py
│   │   ├── test_property_service.py
│   │   └── test_validation_handler.py
│   │
│   ├── Dockerfile
│   ├── alembic.ini
│   └── requirements.txt
│
├── data/
│   └── raw/
│       └── curitiba_apartment_real_estate_data.csv
│
├── frontend/
│
├── scripts/
│   └── postgres/
│       └── init.sql
│
├── .env.example
├── .gitignore
├── AGENTS.md
├── ARCHITECTURE.md
├── CONVENTIONS.md
├── REQUIREMENTS.md
├── docker-compose.yml
└── README.md
```

---

# 🚀 Execução do projeto

## Pré-requisitos

Para executar o projeto localmente:

- Docker;
- Docker Compose;
- Git.

Opcionalmente, para desenvolvimento fora dos containers:

- Python;
- Node.js;
- npm.

---

## Variáveis de ambiente

Crie o arquivo `.env` baseado no:

```text
.env.example
```

Exemplo:

```env
POSTGRES_DB=sdr_imobiliario
POSTGRES_USER=sdr
POSTGRES_PASSWORD=sdr
POSTGRES_PORT=5432

DATABASE_URL=postgresql+psycopg://sdr:sdr@postgres:5432/sdr_imobiliario

BACKEND_PORT=8000
FRONTEND_PORT=3000
```

Não versionar credenciais reais.

---

# 🐳 Docker

Subir a aplicação:

```bash
docker compose up -d
```

Reconstruir o backend:

```bash
docker compose build backend
docker compose up -d backend
```

Verificar containers:

```bash
docker compose ps
```

---

# 🗄️ Banco de dados

O projeto utiliza:

```text
PostgreSQL 16
+
pgvector
```

Imagem Docker:

```text
pgvector/pgvector:pg16
```

A extensão `vector` é habilitada na inicialização do banco.

Para acessar o PostgreSQL:

```bash
docker compose exec postgres psql -U sdr -d sdr_imobiliario
```

Validar pgvector:

```sql
SELECT extname
FROM pg_extension
WHERE extname = 'vector';
```

---

# 🔄 Migrations

O gerenciamento do schema é realizado com **Alembic**.

Aplicar migrations:

```bash
docker compose exec backend alembic upgrade head
```

Verificar migration atual:

```bash
docker compose exec backend alembic current
```

Criar uma migration:

```bash
docker compose exec backend alembic revision --autogenerate -m "descricao da migration"
```

---

# 🌐 API

A API utiliza o prefixo:

```text
/api/v1
```

Principais endpoints implementados:

```text
GET /api/v1/health
GET /api/v1/info
GET /api/v1/info/error
GET /api/v1/properties
```

Documentação Swagger:

```text
http://localhost:8000/docs
```

---

# 🏠 API de imóveis

Endpoint:

```http
GET /api/v1/properties
```

A API permite consultar imóveis persistidos no PostgreSQL utilizando filtros.

Exemplo:

```http
GET /api/v1/properties?neighborhood=Boa%20Vista&min_bedrooms=3&max_price=700000
```

A arquitetura utilizada segue:

```text
Route
  ↓
Service
  ↓
Repository
  ↓
SQLAlchemy
  ↓
PostgreSQL
```

Isso mantém as responsabilidades separadas e facilita testes e futuras evoluções.

---

# 📊 Base de imóveis

Na Missão 04 foi integrada uma base real contendo:

```text
18.760 imóveis
```

O dataset utilizado possui informações como:

```text
usableAreas
totalAreas
suites
bathrooms
bedrooms
parkingSpaces
amenities
description
title
zipCode
lon
lat
street
neighborhood
poisList
yearlyIptu
monthlyCondoFee
price
```

Esses dados são normalizados pelo processo ETL antes da persistência.

O arquivo utilizado pelo projeto é:

```text
data/raw/curitiba_apartment_real_estate_data.csv
```

Tamanho aproximado:

```text
32,49 MB
```

---

# 📦 Fonte e atribuição do Dataset

A base de imóveis utilizada no projeto é o dataset **Curitiba Apartment Prices**, disponibilizado por **Fernando Wittmann** na plataforma Kaggle.

Informações da fonte:

| Informação | Valor |
|---|---|
| Dataset | Curitiba Apartment Prices |
| Autor | Fernando Wittmann |
| Plataforma | Kaggle |
| Cidade | Curitiba — Paraná — Brasil |
| Registros utilizados | 18.760 imóveis |
| Licença declarada | CC0 — Public Domain |
| Arquivo utilizado | `curitiba_apartment_real_estate_data.csv` |
| Tamanho aproximado | 32,49 MB |

Fonte oficial do dataset:

https://www.kaggle.com/datasets/wittmannf/curitiba-apartment-prices/

O dataset é disponibilizado sob licença **CC0 (Public Domain)**, conforme informado na página do dataset no Kaggle.

A base foi incorporada ao projeto para fins acadêmicos e utilizada como fonte de dados para persistência, consultas de imóveis e preparação das etapas posteriores de busca semântica e RAG.

---

# 🔄 ETL de imóveis

O script responsável pela importação está em:

```text
backend/scripts/import_curitiba_properties.py
```

O fluxo é:

```text
CSV
 ↓
Pandas
 ↓
normalização
 ↓
Property
 ↓
external_id
 ↓
verificação de duplicidade
 ↓
PostgreSQL
```

O ETL realiza:

- Leitura do CSV;
- Tratamento de valores nulos;
- Conversão de inteiros;
- Conversão de valores monetários;
- Conversão de listas;
- Normalização de CEP;
- Conversão de latitude e longitude;
- Tratamento de `amenities`;
- Tratamento de pontos de interesse;
- Criação de objetos `Property`;
- Geração de identificador determinístico;
- Verificação de registros existentes;
- Persistência no PostgreSQL.

Executar:

```bash
docker compose exec backend python -m scripts.import_curitiba_properties
```

---

# 🔑 External ID

Cada imóvel possui um:

```text
external_id
```

O identificador é calculado utilizando **SHA-256** sobre os dados normalizados do imóvel.

São considerados atributos relevantes como:

```text
source
title
description
usable_area
total_area
suites
bathrooms
bedrooms
parking_spaces
amenities
zip_code
longitude
latitude
street
neighborhood
pois
yearly_iptu
monthly_condo_fee
price
```

O objetivo é possuir um identificador:

- Determinístico;
- Reproduzível;
- Único;
- Independente do ID sequencial do PostgreSQL.

A coluna possui as restrições:

```text
NOT NULL
UNIQUE
INDEX
```

---

# 🔁 ETL idempotente

A importação foi projetada para ser **idempotente**.

Isso significa que executar o importador novamente não duplica os imóveis já existentes.

Primeira carga:

```text
18.760 imóveis importados
```

Após geração e backfill dos identificadores:

```text
Total de imóveis: 18760
External IDs únicos: 18760
Duplicidades: 0
```

Nova execução do ETL:

```text
Importação concluída:
0 imóveis importados,
18760 ignorados.
```

Portanto:

```text
executar ETL N vezes
        ↓
mesmos 18.760 imóveis
        ↓
sem duplicação
```

---

# 🧪 Testes automatizados

Os testes são executados com:

```text
Pytest
```

Executar toda a regressão:

```bash
docker compose exec backend python -m pytest -v
```

Resultado ao final da Missão 04:

```text
15 passed, 14 warnings in 0.94s
```

Os testes cobrem, entre outros:

- Health check;
- Conexão com PostgreSQL;
- Sessão SQLAlchemy;
- pgvector;
- Schemas;
- Tratamento global de erros;
- Validação de requests;
- Repository de imóveis;
- Service de imóveis;
- API de imóveis;
- Filtros de busca.

---

# 🧪 Estratégia das massas de teste

A base de desenvolvimento possui os 18.760 imóveis reais.

Para impedir que esses registros interfiram nos testes de filtros, os testes utilizam dados controlados, como:

```text
__TEST_PROPERTIES_API__
__TEST_PROPERTY_FILTER__
```

Também são utilizados `external_id` exclusivos para registros de teste.

Os testes da API realizam limpeza da própria massa antes e depois da execução, evitando resíduos que possam causar conflitos com a constraint `UNIQUE`.

Como evolução arquitetural, poderá ser utilizado futuramente um banco exclusivo:

```text
sdr_imobiliario
      ↓
desenvolvimento

sdr_imobiliario_test
      ↓
testes automatizados
```

---

# ⚠️ Tratamento de erros

A API possui tratamento centralizado para diferentes categorias de erro.

Estrutura:

```text
app/core/
├── exceptions.py
└── handlers/
    ├── application_exception.py
    ├── http_exception.py
    └── validation_exception.py
```

Isso permite padronizar as respostas de erro da aplicação.

Exemplo:

```json
{
  "error": "http_error",
  "detail": "Erro de teste"
}
```

---

# ❤️ Health Check

Endpoint:

```http
GET /api/v1/health
```

Exemplo de resposta:

```json
{
  "status": "ok",
  "service": "agente-sdr-imobiliario-api"
}
```

O endpoint possui schema Pydantic específico para sua resposta.

---

# 📚 Missões do projeto

O desenvolvimento está sendo realizado de forma incremental através de missões.

---

# ✅ Missão 01 — Fundação do Projeto

**Status: CONCLUÍDA**

Objetivo:

Criar a estrutura inicial do projeto e garantir que todo o ambiente possa ser executado localmente.

Checklist:

- [x] Repositório criado;
- [x] Estrutura `backend` criada;
- [x] Estrutura `frontend` criada;
- [x] FastAPI configurado;
- [x] Next.js configurado;
- [x] PostgreSQL configurado;
- [x] pgvector habilitado;
- [x] Docker Compose configurado;
- [x] Endpoint `/health`;
- [x] Swagger disponível;
- [x] Comunicação frontend/backend;
- [x] `.env.example`;
- [x] `.gitignore`;
- [x] `README.md`;
- [x] `ARCHITECTURE.md`;
- [x] `AGENTS.md`;
- [x] Testes iniciais com Pytest;
- [x] Projeto executável localmente pelo time.

---

# ✅ Missão 02 — Banco, Sessão e Migrations

**Status: CONCLUÍDA**

Objetivo:

Criar a infraestrutura de persistência da aplicação e preparar o projeto para evolução controlada do banco.

Checklist:

- [x] SQLAlchemy configurado;
- [x] `Base` criada;
- [x] `SessionLocal` criada;
- [x] `get_db` implementado;
- [x] Configuração da conexão centralizada;
- [x] Alembic configurado;
- [x] Baseline criada;
- [x] `alembic upgrade head` validado;
- [x] Conexão com PostgreSQL testada;
- [x] Sessão SQLAlchemy testada;
- [x] pgvector validado;
- [x] Testes executados dentro do container.

Validação da missão:

```text
4 testes PASS
```

---

# ✅ Missão 03 — Estrutura e Padronização da API

**Status: CONCLUÍDA**

Objetivo:

Criar uma estrutura organizada e escalável para a API, padronizando rotas, schemas, configurações e tratamento de erros.

Checklist:

- [x] Estrutura `app/api` criada;
- [x] Estrutura `app/api/routes` criada;
- [x] Router principal criado;
- [x] Prefixo `/api/v1` configurado;
- [x] Rota `/api/v1/health`;
- [x] Schema Pydantic do health;
- [x] Configurações da aplicação centralizadas;
- [x] Estrutura `app/core` criada;
- [x] Rota de informações criada;
- [x] Tratamento de `HTTPException`;
- [x] Tratamento de erros de validação;
- [x] Exceções da aplicação padronizadas;
- [x] Schemas de erro criados;
- [x] Testes de health;
- [x] Testes de info;
- [x] Testes de error handler;
- [x] Testes de error schema;
- [x] Testes de validation handler;
- [x] Swagger validado;
- [x] Organização da API preparada para novas funcionalidades.

Exemplo de tratamento de erro validado:

```json
{
  "error": "http_error",
  "detail": "Erro de teste"
}
```

---

# ✅ Missão 04 — Imóveis, Persistência e Base Real

**Status: CONCLUÍDA**

Objetivo:

Criar o domínio de imóveis, implementar a persistência, disponibilizar consultas pela API e integrar uma base real de imóveis preparada para as próximas etapas de IA e RAG.

## Definition of Done

### Base de dados

- [x] Base real de imóveis selecionada;
- [x] Dataset disponibilizado em `data/raw`;
- [x] Fonte e licença do dataset documentadas;
- [x] Dataset CC0 validado para utilização no projeto;
- [x] CSV acessível pelo backend;
- [x] 18.760 imóveis disponíveis;
- [x] Estrutura do dataset analisada;
- [x] Campos relevantes identificados.

### Modelagem

- [x] Model SQLAlchemy `Property` criado;
- [x] Tabela `properties` criada;
- [x] Migrations criadas com Alembic;
- [x] Schemas Pydantic criados;
- [x] Campos numéricos corretamente tipados;
- [x] Amenities armazenadas;
- [x] Pontos de interesse armazenados;
- [x] Latitude e longitude disponíveis;
- [x] Dados financeiros disponíveis.

### Repository

- [x] `PropertyRepository` criado;
- [x] `save()` implementado;
- [x] `find_by_id()` implementado;
- [x] `find_all()` implementado;
- [x] `find_by_filters()` implementado;
- [x] Filtros de imóveis implementados.

### Service

- [x] `PropertyService` criado;
- [x] Separação entre regra de negócio e persistência;
- [x] Consulta de imóveis através do Service.

### API

- [x] Endpoint `GET /api/v1/properties`;
- [x] Query parameters para filtros;
- [x] Integração Route → Service → Repository;
- [x] Respostas utilizando schemas Pydantic;
- [x] Consulta integrada ao PostgreSQL.

### ETL

- [x] Script de importação criado;
- [x] Leitura do CSV com Pandas;
- [x] Conversão CSV → `Property`;
- [x] Tratamento de valores nulos;
- [x] Conversão de inteiros;
- [x] Conversão de `Decimal`;
- [x] Tratamento de CEP;
- [x] Conversão de `amenities`;
- [x] Conversão de `poisList`;
- [x] Dry-run validado;
- [x] Importação real executada;
- [x] 18.760 imóveis persistidos.

### Idempotência

- [x] `external_id` implementado;
- [x] SHA-256 utilizado;
- [x] Hash baseado nos dados normalizados;
- [x] Validação de colisões implementada;
- [x] 18.760 hashes únicos;
- [x] Zero duplicidades encontradas;
- [x] Backfill dos registros existentes;
- [x] `external_id` preenchido nos 18.760 registros;
- [x] Índice `UNIQUE`;
- [x] Restrição `NOT NULL`;
- [x] ETL preparado para reexecução;
- [x] Registros existentes ignorados automaticamente;
- [x] Segunda execução validada com `0 importados / 18.760 ignorados`.

### Testes

- [x] Testes do Repository;
- [x] Testes do Service;
- [x] Testes da API;
- [x] Massa de teste isolada logicamente dos dados reais;
- [x] `external_id` exclusivo nas massas;
- [x] Cleanup automático dos registros da API;
- [x] Filtros testados;
- [x] Regressão completa executada;
- [x] **15 testes passando**.

Resultado final:

```text
15 passed, 14 warnings in 0.94s
```

## Resultado da Missão 04

Ao final da missão, a aplicação possui:

```text
Curitiba Apartment Prices
         │
         │ 18.760 imóveis
         ▼
        CSV
         │
         ▼
        ETL
         │
         ├── normalização
         ├── external_id SHA-256
         ├── deduplicação
         └── idempotência
         │
         ▼
     PostgreSQL
         │
         ▼
 PropertyRepository
         │
         ▼
  PropertyService
         │
         ▼
GET /api/v1/properties
```

A base de imóveis está preparada para servir como fonte de conhecimento para as próximas etapas do Agente SDR Imobiliário.

---

# 🔮 Próximas evoluções

Com a conclusão da Missão 04, a aplicação possui uma base estruturada de imóveis e está preparada para avançar para as funcionalidades de Inteligência Artificial.

Próximas etapas previstas:

- Preparação dos documentos dos imóveis;
- Estratégia de chunking;
- Geração de embeddings;
- Armazenamento vetorial com pgvector;
- Busca semântica;
- Retrieval;
- RAG;
- Integração com LLM;
- Qualificação do lead;
- Recomendação inteligente de imóveis;
- Evolução da interface do SDR.

---

# 🧠 Evolução prevista para RAG

A evolução arquitetural esperada é:

```text
Cliente
   ↓
Frontend
   ↓
FastAPI
   ↓
Agente SDR
   ↓
Consulta / Retrieval
   ↓
pgvector
   ↓
Imóveis relevantes
   ↓
LLM
   ↓
Resposta contextualizada
```

A base estruturada na Missão 04 será utilizada como fonte para geração dos documentos e embeddings.

---

# 📌 Estado atual

```text
Missão 01 — Fundação do Projeto
✅ CONCLUÍDA

Missão 02 — Banco, Sessão e Migrations
✅ CONCLUÍDA

Missão 03 — Estrutura e Padronização da API
✅ CONCLUÍDA

Missão 04 — Imóveis, Persistência e Base Real
✅ CONCLUÍDA
```

Próxima etapa:

```text
Missão 05
Busca Semântica, Embeddings e pgvector
```

---

# 👥 Projeto acadêmico

Projeto desenvolvido para o Hackathon da Pós-Graduação:

**FIAP — IA para Devs**

Tema:

**Agente SDR Imobiliário com Inteligência Artificial**