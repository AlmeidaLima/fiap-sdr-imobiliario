# AGENTS.md — Agente SDR Imobiliário com IA

## 1. Objetivo deste documento

Este arquivo define as regras operacionais que devem ser seguidas por agentes de IA e ferramentas de desenvolvimento assistido por IA ao trabalhar neste repositório.

O objetivo é permitir que agentes auxiliem no desenvolvimento sem:

- alterar decisões arquiteturais indevidamente;
- introduzir dependências desnecessárias;
- quebrar funcionalidades existentes;
- ignorar testes;
- acessar dados ou recursos de forma inadequada;
- criar implementações incompatíveis com a arquitetura;
- aumentar desnecessariamente a complexidade da POC.

Este documento deve ser consultado antes da execução de qualquer tarefa de desenvolvimento realizada por IA.

---

## 2. Contexto do projeto

O projeto é uma POC de um:

**Agente SDR Imobiliário com IA**

desenvolvido para o Hackathon FIAP.

O agente deverá ser capaz de:

- conversar naturalmente com leads;
- identificar intenção de compra, aluguel ou investimento;
- qualificar leads;
- coletar informações relevantes;
- manter contexto da conversa;
- buscar imóveis compatíveis;
- calcular lead score;
- realizar follow-up;
- permitir agendamento;
- gerar resumo para o corretor;
- futuramente integrar com WhatsApp.

O objetivo principal não é criar apenas um chatbot.

O sistema deverá representar um processo de atendimento comercial imobiliário assistido por IA.

---

## 3. Documentos obrigatórios

Antes de implementar qualquer funcionalidade, o agente deve consultar, quando relevantes:

```text
AGENTS.md
docs/ARCHITECTURE.md
docs/CONVENTIONS.md
docs/REQUIREMENTS.md
skills/
```

A prioridade das regras é:

```text
Solicitação explícita da missão
        ↓
AGENTS.md
        ↓
ARCHITECTURE.md
        ↓
REQUIREMENTS.md
        ↓
CONVENTIONS.md
        ↓
Skill específica
```

Caso exista conflito ou ambiguidade relevante entre documentos, o agente não deve escolher silenciosamente uma interpretação.

Deve informar o conflito antes de realizar uma mudança arquitetural ou comportamental significativa.

---

## 4. Stack oficial do projeto

A stack planejada é:

### Backend

```text
Python
FastAPI
```

### Frontend

```text
React
Next.js
TypeScript
```

### Banco de dados

```text
PostgreSQL
pgvector
```

### Inteligência Artificial

```text
LangGraph
llama.cpp
Qwen ou Gemma
RAG
Embeddings
```

### Integração

```text
Evolution API
```

### Infraestrutura

```text
Docker
Docker Compose
```

### Testes

```text
Pytest
```

O agente não deve substituir tecnologias da stack sem autorização explícita.

---

## 5. Estado atual do projeto

O desenvolvimento é incremental.

O agente nunca deve assumir que todos os componentes descritos na arquitetura já estão implementados.

Antes de iniciar uma tarefa, deve inspecionar o código existente.

Atualmente, a fundação inclui:

```text
Next.js
FastAPI
PostgreSQL
pgvector
Docker
Docker Compose
GET /health
Swagger
Comunicação frontend → backend
```

Componentes como LangGraph, llama.cpp, RAG, memória, lead scoring e Evolution API serão adicionados progressivamente.

Não implementar antecipadamente funcionalidades pertencentes a missões futuras sem solicitação.

---

# 6. Regra principal de desenvolvimento

Sempre implementar:

> a menor alteração capaz de atender corretamente à tarefa atual.

Evitar:

- overengineering;
- abstrações prematuras;
- frameworks desnecessários;
- funcionalidades não solicitadas;
- refatorações sem relação com a tarefa;
- dependências sem necessidade real.

A POC deve permanecer simples, compreensível e demonstrável.

---

## 7. Arquitetura obrigatória

O fluxo principal de backend deve respeitar:

```text
HTTP Request
     ↓
FastAPI Route
     ↓
Service
     ↓
Repository
     ↓
PostgreSQL
```

Para operações realizadas pelo agente:

```text
Usuário
   ↓
FastAPI
   ↓
LangGraph
   ↓
LLM
   ↓
Tool
   ↓
Service
   ↓
Repository
   ↓
PostgreSQL
```

O agente de IA responsável por desenvolver código não deve violar essas fronteiras.

---

## 8. Guardrail — acesso ao banco

O LLM da aplicação nunca deve possuir acesso direto ao PostgreSQL.

PROIBIDO:

```text
LLM
 ↓
SQL
 ↓
PostgreSQL
```

OBRIGATÓRIO:

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

O modelo pode decidir utilizar uma tool.

A tool controla quais operações podem ser realizadas.

---

## 9. Guardrail — dados de imóveis

O LLM não deve inventar:

- imóveis;
- preços;
- endereços;
- quantidade de quartos;
- metragem;
- disponibilidade;
- características objetivas.

Dados objetivos deverão vir da base estruturada.

Fluxo:

```text
Pergunta
   ↓
Tool
   ↓
PropertyService
   ↓
PropertyRepository
   ↓
PostgreSQL
```

O LLM pode explicar, organizar e apresentar os resultados.

Não pode fabricar resultados ausentes.

---

## 10. Guardrail — SQL versus RAG

Dados estruturados devem utilizar PostgreSQL.

Exemplos:

```text
preço
bairro
cidade
quartos
banheiros
área
tipo
disponibilidade
```

Conhecimento textual poderá utilizar RAG.

Exemplos:

```text
informações sobre bairros
FAQs
documentação
políticas
financiamento
descrições textuais
conteúdo imobiliário
```

Não utilizar RAG para substituir consultas estruturadas quando SQL for mais apropriado.

---

## 11. Guardrail — regras determinísticas

Regras críticas não devem depender exclusivamente do LLM.

Exemplos:

```text
Lead Score
validações
permissões
estados
regras de negócio
operações no banco
```

Exemplo correto:

```text
LLM identifica:
urgencia = 30 dias

        ↓

LeadScoreService

        ↓

+25 pontos
```

O LLM interpreta linguagem.

O código aplica a regra.

---

## 12. Guardrail — segurança

Nunca adicionar ao repositório:

```text
senhas
tokens
API keys
credenciais
.env
dados pessoais reais desnecessários
```

Utilizar variáveis de ambiente.

Exemplo:

```python
import os

database_url = os.getenv("DATABASE_URL")
```

Não utilizar:

```python
database_url = "postgresql://usuario:senha@..."
```

Secrets nunca devem aparecer em logs.

---

## 13. Guardrail — dependências

Não adicionar bibliotecas apenas por conveniência.

Antes de adicionar uma dependência, verificar:

1. se o problema pode ser resolvido com a stack atual;
2. se a dependência é realmente necessária;
3. se é compatível com o projeto;
4. se aumenta significativamente a complexidade;
5. se possui licença adequada.

Dependências novas devem possuir justificativa técnica.

---

## 14. Guardrail — arquitetura

O agente não pode alterar decisões arquiteturais significativas sem autorização.

Exemplos:

```text
trocar PostgreSQL
trocar FastAPI
trocar Next.js
trocar LangGraph
trocar mecanismo de RAG
trocar estratégia de persistência
introduzir novo framework
alterar fronteiras entre camadas
```

Se identificar uma alternativa potencialmente melhor, deve:

```text
identificar problema
      ↓
explicar alternativa
      ↓
apresentar vantagens/desvantagens
      ↓
aguardar decisão
```

Não implementar silenciosamente.

---

## 15. Regras do FastAPI

As rotas devem ser simples.

Exemplo esperado:

```python
@router.post("/leads")
def create_lead(request: LeadRequest):
    return lead_service.create(request)
```

Evitar:

```python
@router.post("/leads")
def create_lead(request):
    # validações complexas
    # queries SQL
    # cálculo de score
    # integração com LLM
    # persistência
    # outras regras
```

Regras devem ser delegadas para services.

---

## 16. Regras dos Services

Services representam regras e casos de uso.

Exemplos:

```text
LeadService
PropertyService
ConversationService
LeadScoreService
FollowUpService
SchedulingService
```

Services podem coordenar repositories e integrações.

Não devem depender de detalhes da interface do frontend.

---

## 17. Regras dos Repositories

Repositories são responsáveis pelo acesso aos dados.

Exemplos:

```text
LeadRepository
PropertyRepository
ConversationRepository
AppointmentRepository
```

Devem concentrar operações de persistência e consultas.

O restante da aplicação não deve espalhar SQL arbitrariamente.

---

## 18. Regras das Tools

Tools são operações disponibilizadas ao agente de IA.

Exemplos:

```text
buscar_imoveis
consultar_lead
salvar_preferencias
calcular_lead_score
agendar_visita
```

Cada tool deve:

- possuir responsabilidade clara;
- validar entrada;
- limitar o escopo da operação;
- chamar service apropriado;
- retornar dados estruturados;
- tratar erros previsíveis.

Tools não devem fornecer acesso genérico ao banco.

PROIBIDO:

```text
executar_sql(query)
```

Preferir:

```text
buscar_imoveis(filtros)
```

---

## 19. Regras do RAG

O pipeline deve seguir conceitualmente:

```text
Documento
 ↓
Extração
 ↓
Chunking
 ↓
Embedding
 ↓
pgvector
 ↓
Retrieval
 ↓
Contexto
 ↓
LLM
```

A resposta deve ser baseada no conteúdo recuperado quando a pergunta depender da base de conhecimento.

Quando não houver informação suficiente, o sistema deve preferir indicar ausência de informação em vez de inventar conteúdo.

---

## 20. Regras do Frontend

O frontend deve:

- consumir APIs do backend;
- evitar regras de negócio críticas;
- manter componentes simples;
- separar apresentação de comunicação com APIs;
- utilizar TypeScript;
- tratar estados de carregamento e erro;
- evitar URLs espalhadas pelo código.

URLs e configurações deverão utilizar variáveis de ambiente ou configuração centralizada.

---

## 21. Testes são obrigatórios

Toda funcionalidade relevante deve possuir testes compatíveis com seu nível.

Tipos:

```text
unitário
integração
API
agente
E2E
```

Nem toda funcionalidade necessita de todos os níveis.

A estratégia deve ser proporcional ao risco.

---

## 22. Regras para testes

O agente nunca deve:

- apagar um teste apenas porque ele falhou;
- enfraquecer uma assertion para fazer o teste passar;
- ignorar silenciosamente testes quebrados;
- alterar o resultado esperado apenas para adaptar ao código incorreto.

Quando um teste falhar:

```text
Teste falhou
     ↓
Investigar causa
     ↓
Código está errado?
     │
     ├── Sim → corrigir código
     │
     └── Não
          ↓
Requisito mudou?
          │
          ├── Sim → justificar alteração do teste
          └── Não → investigar novamente
```

---

## 23. Pytest

O backend utilizará Pytest.

Testes deverão ficar preferencialmente em:

```text
backend/tests/
```

Exemplo:

```text
backend/tests/
├── unit/
├── integration/
└── api/
```

A estrutura deverá crescer apenas quando houver testes suficientes para justificar as subdivisões.

---

## 24. Workflow obrigatório do agente

Para cada tarefa, seguir este processo:

```text
1. Entender a tarefa
        ↓
2. Ler AGENTS.md
        ↓
3. Consultar documentos relevantes
        ↓
4. Procurar skill aplicável
        ↓
5. Inspecionar código existente
        ↓
6. Criar plano curto
        ↓
7. Implementar menor mudança necessária
        ↓
8. Executar testes
        ↓
9. Executar validações
        ↓
10. Corrigir falhas
        ↓
11. Repetir testes
        ↓
12. Verificar critérios de aceitação
        ↓
13. Apresentar resultado
```

Não declarar uma tarefa concluída antes das validações.

---

## 25. Loop de implementação

O agente deverá trabalhar em loop até atingir o resultado esperado:

```text
Implementar
    ↓
Testar
    ↓
Passou?
 ┌──┴──┐
Não   Sim
 │      │
 ▼      ▼
Analisar  Validar critérios
 │
 ▼
Corrigir
 │
 └──────→ Testar novamente
```

O objetivo não é gerar código rapidamente.

O objetivo é gerar uma alteração verificável.

---

## 26. Antes de alterar código

O agente deve primeiro inspecionar:

- arquivos relacionados;
- implementação existente;
- testes existentes;
- configurações;
- dependências;
- documentação relevante.

Não deve substituir arquivos inteiros sem necessidade quando uma alteração menor for suficiente.

---

## 27. Escopo da missão

Cada missão deve possuir escopo limitado.

Se a missão for:

```text
Implementar busca de imóveis
```

o agente não deverá simultaneamente:

```text
refatorar autenticação
trocar framework
implementar WhatsApp
alterar frontend inteiro
introduzir microserviços
```

Mudanças não relacionadas devem ficar fora da missão.

---

## 28. Skills

Antes de executar uma tarefa recorrente, verificar:

```text
skills/
```

Se existir uma skill correspondente, ela deverá ser utilizada como orientação.

Exemplos planejados:

```text
skills/
├── create-fastapi-endpoint.md
├── create-pytest-test.md
├── create-service.md
├── create-repository.md
└── review-code.md
```

Skills não podem contradizer `AGENTS.md` ou `ARCHITECTURE.md`.

---

## 29. Criação de novas Skills

Uma nova skill pode ser criada quando:

- uma tarefa ocorrer repetidamente;
- existir um padrão claro;
- houver benefício em padronizar a execução.

Uma skill deve preferencialmente possuir:

```text
Objetivo
Contexto
Pré-condições
Passos
Regras
Guardrails
Critérios de aceitação
Validações
```

Não criar skills para tarefas únicas sem necessidade.

---

## 30. Definition of Done para tarefas

Uma tarefa só pode ser declarada concluída quando aplicável:

```text
[ ] Requisito implementado
[ ] Arquitetura respeitada
[ ] Código organizado
[ ] Testes criados/atualizados
[ ] Testes executados
[ ] Testes passando
[ ] Aplicação executando
[ ] Critérios de aceitação validados
[ ] Documentação atualizada
[ ] Nenhum secret adicionado
[ ] Nenhuma regressão conhecida
```

Itens não aplicáveis podem ser explicitamente informados.

---

## 31. Evidências obrigatórias

Ao concluir uma tarefa, o agente deve informar:

### Arquivos alterados

Exemplo:

```text
backend/app/api/leads.py
backend/app/services/lead_service.py
backend/tests/api/test_leads.py
```

### Testes executados

Exemplo:

```text
pytest backend/tests/api/test_leads.py
```

### Resultado

Exemplo:

```text
5 passed
```

### Critérios validados

Exemplo:

```text
POST /leads → 201
payload inválido → 422
lead persistido → confirmado
```

Não afirmar simplesmente:

```text
"Pronto."
```

sem apresentar evidência suficiente.

---

## 32. Tratamento de falhas

Se uma tarefa não puder ser concluída, o agente deverá informar:

```text
o que falhou
por que falhou
qual evidência existe
qual impacto
qual próximo passo recomendado
```

Não esconder erros.

Não simular sucesso.

---

## 33. Dados de teste

Preferir dados:

- fictícios;
- controlados;
- reproduzíveis;
- determinísticos.

Evitar utilizar dados pessoais reais.

Testes automatizados não devem depender desnecessariamente de serviços externos.

---

## 34. Logs

Logs devem ajudar a diagnosticar problemas.

Podem registrar:

```text
início/fim de operações relevantes
erros
tools utilizadas
tempo de execução
identificadores técnicos
```

Não devem registrar:

```text
senhas
tokens
API keys
secrets
dados sensíveis desnecessários
```

---

## 35. Git

O agente deve manter alterações pequenas e relacionadas à tarefa.

Não incluir arquivos gerados ou locais, como:

```text
.env
.idea/
.venv/
node_modules/
.next/
*.gguf
```

Antes de sugerir commit, verificar os arquivos alterados.

---

## 36. Commits

Utilizar mensagens objetivas.

Padrão recomendado:

```text
feat: ...
fix: ...
test: ...
docs: ...
refactor: ...
chore: ...
```

Exemplos:

```text
feat: add property search endpoint

test: add health endpoint tests

docs: document project architecture

chore: configure docker environment
```

Não criar commits com alterações não relacionadas.

---

## 37. Mudanças destrutivas

O agente não deve executar operações destrutivas sem autorização explícita.

Exemplos:

```text
DROP DATABASE
DROP TABLE
DELETE sem filtro
docker compose down -v
remoção de arquivos importantes
reset de Git
force push
```

Se uma operação destrutiva for necessária, explicar primeiro:

```text
ação
impacto
motivo
alternativa
```

e aguardar autorização.

---

## 38. Banco de dados

Mudanças de schema devem ser controladas.

O agente não deve alterar tabelas arbitrariamente durante a execução da aplicação.

Quando o projeto introduzir migrations, elas deverão ser utilizadas como mecanismo oficial de evolução do banco.

---

## 39. Comportamento diante de ambiguidade

Se houver uma ambiguidade pequena que não afeta arquitetura ou comportamento relevante, o agente poderá escolher a alternativa mais simples e registrar a decisão.

Se a ambiguidade afetar:

- arquitetura;
- segurança;
- dados;
- requisito;
- comportamento funcional;
- integração externa;

o agente deverá solicitar decisão antes de implementar.

---

## 40. Não inventar requisitos

O agente não deve transformar suposições em requisitos.

Se `REQUIREMENTS.md` não definir determinado comportamento, não assumir silenciosamente que ele é obrigatório.

Pode sugerir uma alternativa, mas deve diferenciá-la do requisito existente.

---

## 41. Princípio de simplicidade

Quando existirem duas soluções que atendem igualmente aos requisitos, preferir:

```text
menor complexidade
menor acoplamento
menos dependências
maior testabilidade
maior clareza
```

O projeto é uma POC de Hackathon.

Simplicidade e capacidade de demonstração possuem prioridade sobre arquitetura excessivamente sofisticada.

---

## 42. Princípio de rastreabilidade

Toda funcionalidade deve ser relacionável a:

```text
Requisito
   ↓
Implementação
   ↓
Teste
   ↓
Evidência
```

Esse princípio é especialmente importante para funcionalidades críticas da demonstração.

---

## 43. Critério final para agentes

Antes de declarar uma missão concluída, o agente deve conseguir responder:

```text
O que foi solicitado?

O que foi implementado?

Quais arquivos foram alterados?

Quais testes foram executados?

Todos passaram?

Os critérios de aceitação foram atendidos?

A arquitetura foi respeitada?

Foi adicionada alguma dependência?

Existe algum risco ou pendência?
```

Se essas respostas não estiverem claras, a missão ainda não está pronta para ser considerada concluída.

---

## 44. Regra central

O agente de desenvolvimento deve atuar como um engenheiro dentro de um sistema com regras, e não como um gerador irrestrito de código.

O ciclo esperado é:

```text
Entender
   ↓
Planejar
   ↓
Implementar
   ↓
Testar
   ↓
Verificar
   ↓
Corrigir
   ↓
Evidenciar
```

A qualidade da implementação é determinada não apenas pelo código produzido, mas pela capacidade de demonstrar que o comportamento esperado foi realmente atendido.

## Execução e validação do projeto

Antes de implementar uma tarefa, o agente deve consultar o `README.md` para verificar as instruções atualizadas de execução.

O comando padrão para subir o ambiente é:

```bash
docker compose up --build -d
```

Para verificar os serviços:

```bash
docker compose ps
```

Para executar os testes do backend:

```bash
docker compose exec backend python -m pytest -v
```

Antes de declarar uma alteração concluída, o agente deve garantir que o ambiente continue executando corretamente.

O `README.md` é a fonte oficial para comandos de instalação, execução e validação do ambiente.

O agente não deve inventar comandos de inicialização diferentes quando o procedimento já estiver documentado no README.