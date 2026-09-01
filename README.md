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
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── database/
│   │   ├── integrations/
│   │   ├── models/
│   │   ├── rag/
│   │   ├── services/
│   │   └── tools/
│   ├── tests/
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

Resultado esperado:

```text
tests/test_health.py::test_health_returns_status_ok PASSED
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
[ ] http://localhost:3000 apresenta o frontend
[ ] frontend informa que está conectado ao backend
[ ] PostgreSQL responde ao SELECT 1
[ ] extensão vector está disponível
[ ] Pytest executa com sucesso dentro do backend
```