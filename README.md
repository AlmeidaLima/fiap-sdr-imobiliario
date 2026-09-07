# Agente SDR Imobiliário com IA

POC desenvolvida para o Hackathon FIAP com o objetivo de criar um agente SDR imobiliário com IA capaz de qualificar leads, manter contexto de conversação, buscar imóveis e apoiar o atendimento comercial.

## Status do projeto

Projeto em desenvolvimento.

### Missão 01 — Fundação do projeto

- [x] Repositório criado
- [x] Estrutura de diretórios criada
- [x] FastAPI executando
- [x] Next.js executando
- [x] PostgreSQL executando
- [x] pgvector habilitado
- [x] Docker Compose funcionando
- [x] Endpoint `/health` funcionando
- [x] Swagger disponível
- [x] Frontend comunicando com backend
- [x] `.env.example` criado
- [x] `.gitignore` criado
- [x] README criado
- [x] ARCHITECTURE criado
- [x] AGENTS criado
- [x] Primeiros testes Pytest executando
- [ ] Todos os integrantes conseguem executar o projeto

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
- [x] Migration baseline `64bbb5ca46ba` criada e versionada
- [x] Ciclo de migrations validado
- [x] Suíte completa executada no Docker: **4 testes passando**

#### Persistência

A camada de persistência utiliza **SQLAlchemy 2.x**, **psycopg 3**, **PostgreSQL 16** e **pgvector**. A conexão é configurada pela variável `DATABASE_URL`. A configuração geral da aplicação, incluindo a URL do banco, está centralizada em `backend/app/core/config.py`. O gerenciamento de sessões é realizado por `SessionLocal` e `get_db()` em `backend/app/database/session.py`, e a Base declarativa fica em `backend/app/database/base.py`.

A arquitetura básica da persistência é:

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
psycopg 3
   │
   ▼
PostgreSQL + pgvector
```

#### Migrations

As alterações de estrutura do banco são controladas pelo **Alembic**. A configuração está em `backend/alembic.ini` e `backend/alembic/`, utilizando a mesma `DATABASE_URL` da aplicação e `Base.metadata` como metadata dos models.

Comandos principais:

```bash
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
docker compose exec backend alembic history
```

A migration inicial de baseline é `64bbb5ca46ba_baseline.py`. As migrations devem ser versionadas no Git e não devem existir somente dentro do container.

#### Testes da camada de banco

A Missão 02 adicionou os seguintes testes:

```text
test_database_connection.py  → conexão SQLAlchemy → PostgreSQL
test_database_session.py     → gerenciamento de sessão
test_pgvector.py             → disponibilidade da extensão vector
test_health.py               → regressão do healthcheck
```

Validação final realizada dentro do Docker:

```text
4 passed, 2 warnings
```

Os warnings atuais são avisos de depreciação das dependências de teste e não impediram a execução da suíte.


### Missão 03 — Estrutura da API

**Status: Concluída**

- [x] Endpoint `/health` separado em router próprio
- [x] Schema Pydantic `HealthResponse` criado
- [x] Configurações da aplicação centralizadas em `app/core/config.py`
- [x] `DATABASE_URL` integrada ao `Settings`
- [x] SQLAlchemy e Alembic utilizando a mesma fonte de configuração
- [x] Router principal da API criado
- [x] Versionamento de endpoints definido com prefixo `/api/v1`
- [x] Endpoint técnico `/api/v1/info` criado
- [x] Schema Pydantic `InfoResponse` criado
- [x] Tratamento padronizado de `HTTPException`
- [x] Exceção própria `ApplicationException` criada
- [x] Tratamento padronizado de erros de validação `422`
- [x] Schema `ErrorResponse` criado
- [x] Contratos de erro documentados no Swagger
- [x] Testes do healthcheck, info, handlers e schemas criados
- [x] Regressão completa executada no Docker

#### Organização da API

A aplicação passou a separar endpoints técnicos dos endpoints versionados de negócio:

```text
GET /health
    → endpoint técnico da aplicação

/api/v1/*
    → endpoints versionados da API
```

O router principal está em:

```text
backend/app/api/router.py
```

Os endpoints específicos ficam em:

```text
backend/app/api/routes/
```

Atualmente estão disponíveis:

```text
GET /health
GET /api/v1/info
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

Essa configuração é reutilizada pelo FastAPI, SQLAlchemy, Alembic e pelos endpoints que precisam expor informações da aplicação.

#### Schemas Pydantic

Os contratos de resposta foram separados em `backend/app/schemas/`:

```text
health.py  → HealthResponse
info.py    → InfoResponse
error.py   → ErrorResponse
```

Isso permite tipar as respostas da API e documentar seus contratos automaticamente no Swagger.

#### Tratamento de erros

A aplicação possui handlers centralizados em:

```text
backend/app/core/handlers/
```

São tratados:

```text
HTTPException
ApplicationException
RequestValidationError (422)
```

O formato padrão de erro é baseado em:

```json
{
  "error": "application_error",
  "detail": "Descrição do erro"
}
```

Erros de validação também seguem o mesmo envelope, com `detail` contendo a lista de validações retornadas pelo FastAPI/Pydantic.

#### Testes adicionados na Missão 03

A missão adicionou ou ampliou testes para:

```text
test_health.py               → healthcheck e contrato de resposta
test_info.py                 → endpoint versionado /api/v1/info
test_error_handler.py        → tratamento de ApplicationException
test_validation_handler.py   → tratamento de validação 422
test_error_schema.py         → contrato ErrorResponse
```

A regressão completa deve ser executada com:

```bash
docker compose exec backend python -m pytest -v
```

## Stack

Tecnologias definidas para o projeto:

- Python
- FastAPI
- React
- Next.js
- PostgreSQL
- pgvector
- Docker
- Docker Compose
- Pytest

Tecnologias planejadas para as próximas etapas:

- LangGraph
- llama.cpp
- Modelo local Qwen ou Gemma
- RAG
- Evolution API

## Estrutura do projeto

```text
fiap-sdr-imobiliario/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   │   ├── router.py
│   │   │   └── routes/
│   │   │       ├── health.py
│   │   │       └── info.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── exceptions.py
│   │   │   └── handlers/
│   │   │       ├── application_exception.py
│   │   │       ├── http_exception.py
│   │   │       └── validation_exception.py
│   │   ├── database/
│   │   │   ├── base.py
│   │   │   └── session.py
│   │   ├── integrations/
│   │   ├── models/
│   │   ├── rag/
│   │   ├── schemas/
│   │   │   ├── error.py
│   │   │   ├── health.py
│   │   │   └── info.py
│   │   ├── services/
│   │   └── tools/
│   ├── tests/
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
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONVENTIONS.md
│   └── REQUIREMENTS.md
│
├── scripts/
│   └── postgres/
│       └── init.sql
├── skills/
├── .env.example
├── .gitignore
├── AGENTS.md
├── compose.yaml
└── README.md
```

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

O projeto disponibiliza o arquivo:

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

### 3. Subir o ambiente

Na raiz do projeto execute:

```bash
docker compose up --build -d
```

O Docker Compose iniciará os serviços:

```text
frontend
backend
postgres
```

---

### 4. Verificar os containers

Execute:

```bash
docker compose ps
```

Os serviços deverão aparecer em execução.

---

### 5. Acessar a aplicação

Frontend:

```text
http://localhost:3000
```

Backend:

```text
http://localhost:8000
```

Health Check:

```text
http://localhost:8000/health
```

Informações da API:

```text
http://localhost:8000/api/v1/info
```

Swagger:

```text
http://localhost:8000/docs
```

---

### 6. Executar os testes

Os testes do backend podem ser executados dentro do Docker:

```bash
docker compose exec backend python -m pytest -v
```

Resultado esperado: todos os testes devem passar. A suíte atualmente cobre:

```text
Conexão com PostgreSQL
Gerenciamento de sessão SQLAlchemy
Healthcheck e schema de resposta
Endpoint /api/v1/info
pgvector
ApplicationException
Erros de validação 422
Schema padronizado de erros
```

---

### 7. Verificar PostgreSQL

```bash
docker compose exec postgres psql -U sdr -d sdr_imobiliario -c "SELECT 1;"
```

---

### 8. Verificar pgvector

```bash
docker compose exec postgres psql -U sdr -d sdr_imobiliario -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

A extensão `vector` deverá estar disponível.

---

### 9. Visualizar logs

Todos os serviços:

```bash
docker compose logs -f
```

Somente backend:

```bash
docker compose logs -f backend
```

Somente frontend:

```bash
docker compose logs -f frontend
```

---

### 10. Parar o ambiente

```bash
docker compose down
```

Esse comando interrompe os containers sem remover o volume do PostgreSQL.

> Não utilize `docker compose down -v` sem necessidade, pois `-v` remove os volumes e pode apagar os dados locais do PostgreSQL.

---

## Validação rápida do ambiente

Após subir o projeto, valide:

```text
[ ] docker compose ps apresenta os serviços ativos
[ ] http://localhost:8000/health retorna status "ok"
[ ] http://localhost:8000/docs apresenta o Swagger
[ ] http://localhost:8000/api/v1/info retorna nome e versão da API
[ ] http://localhost:3000 apresenta o frontend
[ ] frontend informa que está conectado ao backend
[ ] PostgreSQL responde ao SELECT 1
[ ] extensão vector está disponível
[ ] Pytest executa com sucesso dentro do backend
```