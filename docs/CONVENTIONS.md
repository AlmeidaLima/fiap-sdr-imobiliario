# Convenções de Desenvolvimento — Agente SDR Imobiliário com IA

## 1. Objetivo

Este documento define convenções de código, estrutura, nomenclatura, testes e colaboração utilizadas no projeto.

O objetivo é manter consistência entre código escrito manualmente e código produzido com auxílio de agentes de IA.

Este documento complementa:

```text
AGENTS.md
docs/ARCHITECTURE.md
docs/REQUIREMENTS.md
```

---

## 2. Princípios gerais

O desenvolvimento deverá priorizar:

```text
clareza
simplicidade
testabilidade
baixo acoplamento
responsabilidade única
manutenibilidade
```

Evitar:

```text
overengineering
abstrações prematuras
duplicação desnecessária
dependências desnecessárias
arquivos excessivamente grandes
métodos com múltiplas responsabilidades
```

---

## 3. Idioma

### Código

Nomes técnicos de:

- classes;
- funções;
- métodos;
- variáveis;
- módulos;
- endpoints;

devem preferencialmente utilizar **inglês**.

Exemplo:

```python
class LeadService:
    pass
```

Preferir:

```python
def calculate_lead_score():
    pass
```

Evitar:

```python
def calcular_pontuacao_lead():
    pass
```

---

### Documentação

Documentação do projeto poderá permanecer em português.

Exemplos:

```text
README.md
ARCHITECTURE.md
REQUIREMENTS.md
CONVENTIONS.md
AGENTS.md
```

---

### Mensagens apresentadas ao usuário

A interface conversacional deverá inicialmente priorizar português do Brasil.

---

## 4. Python

O backend deverá utilizar código Python simples e legível.

### Nomenclatura

Classes:

```python
LeadService
PropertyService
LeadRepository
```

Funções e métodos:

```python
create_lead()
find_properties()
calculate_score()
```

Variáveis:

```python
lead_id
max_price
property_type
```

Constantes:

```python
MAX_SCORE = 100
DEFAULT_LIMIT = 10
```

---

## 5. Type Hints

Funções relevantes devem utilizar type hints.

Preferir:

```python
def calculate_score(lead: Lead) -> int:
    ...
```

Evitar:

```python
def calculate_score(lead):
    ...
```

Isso melhora:

- clareza;
- suporte da IDE;
- manutenção;
- geração assistida por IA;
- testabilidade.

---

## 6. FastAPI

Endpoints deverão ser organizados por domínio.

Exemplo futuro:

```text
backend/app/api/
├── health.py
├── leads.py
├── properties.py
└── conversations.py
```

Evitar concentrar todos os endpoints em `main.py`.

O `main.py` deverá principalmente:

```text
criar aplicação
configurar aplicação
registrar routers
```

---

## 7. Rotas

URLs devem utilizar substantivos.

Preferir:

```text
GET /leads
GET /leads/{lead_id}
POST /leads

GET /properties
GET /properties/{property_id}
```

Evitar:

```text
/getLead
/createLead
/searchPropertiesNow
```

---

## 8. Schemas

Objetos de entrada e saída da API deverão utilizar schemas explícitos.

Exemplo:

```python
class CreateLeadRequest(BaseModel):
    name: str
    intent: str
```

Quando necessário, separar:

```text
CreateLeadRequest
LeadResponse
UpdateLeadRequest
```

Não retornar diretamente estruturas internas quando isso expuser detalhes desnecessários.

---

## 9. Services

Services deverão representar casos de uso ou regras de negócio.

Exemplo:

```python
class LeadService:

    def create_lead(self, request: CreateLeadRequest):
        ...
```

Evitar services genéricos como:

```text
UtilsService
GenericService
CommonService
```

quando não houver uma responsabilidade de domínio clara.

---

## 10. Repositories

Repositories deverão encapsular acesso a dados.

Exemplos:

```python
LeadRepository
PropertyRepository
ConversationRepository
```

Métodos devem indicar intenção.

Preferir:

```python
find_by_id()
find_by_filters()
save()
update()
```

Evitar permitir execução arbitrária de SQL fora da camada de persistência.

---

## 11. Tools do agente

Nomes das tools devem representar ações específicas.

Preferir:

```text
search_properties
get_lead
save_preferences
calculate_lead_score
schedule_visit
```

Evitar tools excessivamente genéricas:

```text
execute
run_command
execute_sql
database_query
```

Entradas e saídas devem ser estruturadas.

---

## 12. LangGraph

Nodes devem possuir uma responsabilidade clara.

Exemplo conceitual:

```text
identify_intent
extract_preferences
qualify_lead
search_properties
schedule_appointment
generate_response
```

Evitar um único node responsável por todo o processo.

O estado do grafo deverá possuir estrutura explícita.

---

## 13. Configuração

Variáveis de ambiente deverão utilizar:

```text
UPPER_SNAKE_CASE
```

Exemplo:

```text
DATABASE_URL
BACKEND_PORT
FRONTEND_PORT
LLM_BASE_URL
```

Configurações não devem ficar espalhadas pelo código.

---

## 14. Arquivos .env

O projeto utilizará:

```text
.env.example
```

como documentação das variáveis necessárias.

Nunca adicionar credenciais reais ao `.env.example`.

O arquivo:

```text
.env
```

deve permanecer ignorado pelo Git.

---

## 15. Frontend

Componentes React devem possuir responsabilidades claras.

Nomes:

```text
LeadCard
LeadList
ConversationPanel
PropertyCard
AppointmentForm
```

Evitar componentes como:

```text
Component1
NewComponent
GenericComponent
```

---

## 16. TypeScript

Evitar `any` quando o tipo puder ser definido.

Preferir:

```typescript
type Lead = {
  id: string;
  name: string;
  score: number;
};
```

Evitar:

```typescript
const lead: any = ...
```

Tipos compartilhados deverão ser centralizados quando houver benefício real.

---

## 17. Comunicação com API

Chamadas HTTP não devem ser espalhadas arbitrariamente pelos componentes.

Preferir uma camada como:

```text
frontend/
└── services/
    ├── api.ts
    ├── leads.ts
    └── properties.ts
```

A estrutura definitiva deverá ser introduzida quando houver necessidade.

Não criar camadas vazias antecipadamente.

---

## 18. Formatação

O projeto deverá utilizar a formatação padrão das linguagens e ferramentas utilizadas.

Python deve seguir estilo compatível com PEP 8.

TypeScript deve respeitar a configuração de lint do projeto Next.js.

Não realizar formatações massivas sem relação com a tarefa atual.

---

## 19. Imports

Organizar imports de forma legível.

Python:

```python
import os

from fastapi import APIRouter

from app.services.lead_service import LeadService
```

Evitar imports não utilizados.

---

## 20. Funções

Preferir funções pequenas com responsabilidade específica.

Se uma função:

- valida dados;
- consulta banco;
- calcula score;
- chama LLM;
- envia mensagem;

provavelmente possui responsabilidades demais.

Dividir quando isso melhorar significativamente a clareza e a testabilidade.

---

## 21. Comentários

Comentários devem explicar principalmente o **porquê**, não repetir o código.

Evitar:

```python
# Soma 1
value += 1
```

Preferir:

```python
# Leads com visita confirmada recebem prioridade comercial adicional.
score += VISIT_ACCEPTED_SCORE
```

Não adicionar comentários desnecessários em cada linha.

---

## 22. Docstrings

Utilizar docstrings quando elas adicionarem contexto útil.

Especialmente em:

- regras complexas;
- serviços públicos;
- integrações;
- algoritmos;
- comportamentos não evidentes.

Funções triviais não precisam de documentação excessiva.

---

## 23. Tratamento de erros

Não utilizar:

```python
except Exception:
    pass
```

Falhas devem:

- ser tratadas quando previsíveis;
- ser registradas quando relevante;
- produzir respostas coerentes;
- preservar informação útil para diagnóstico.

Não expor stack traces internos diretamente ao usuário final.

---

## 24. Logs

Preferir logs estruturados e objetivos.

Exemplo:

```python
logger.info("property_search_started", extra={"lead_id": lead_id})
```

Logs deverão evitar secrets e informações sensíveis.

---

## 25. Testes

Nome dos arquivos:

```text
test_health.py
test_lead_service.py
test_property_repository.py
```

Nome dos testes:

```python
def test_should_return_health_status_ok():
    ...
```

ou:

```python
def test_health_returns_ok():
    ...
```

Escolher um padrão simples e manter consistência.

---

## 26. Estrutura inicial de testes

Enquanto a suíte for pequena:

```text
backend/tests/
├── test_health.py
└── ...
```

Quando crescer:

```text
backend/tests/
├── unit/
├── integration/
└── api/
```

Não criar subdivisões desnecessárias antes de existirem testes suficientes.

---

## 27. Testes determinísticos

Testes devem produzir o mesmo resultado quando executados repetidamente.

Evitar dependências desnecessárias de:

```text
hora atual
internet
serviços externos
LLM real
dados aleatórios não controlados
```

Quando necessário, utilizar:

```text
mocks
fixtures
dados fixos
injeção de dependência
```

---

## 28. Testes do LLM

Não depender exclusivamente de igualdade exata de texto.

Evitar:

```python
assert response == "Olá, João. Como posso ajudar?"
```

quando a resposta for generativa.

Preferir validar:

```text
estrutura
campos extraídos
tool selecionada
estado resultante
restrições
presença de informação obrigatória
```

Respostas naturais poderão ser avaliadas separadamente.

---

## 29. Testes de API

Validar quando aplicável:

```text
status HTTP
schema
campos obrigatórios
resposta válida
erros esperados
efeitos no banco
```

---

## 30. Fixtures

Fixtures reutilizáveis podem ser utilizadas quando reduzirem duplicação.

Exemplo:

```python
@pytest.fixture
def sample_lead():
    ...
```

Não criar fixtures genéricas difíceis de entender.

---

## 31. Dados de teste

Utilizar dados fictícios.

Exemplo:

```text
João Teste
Maria Exemplo
lead@example.com
```

Não utilizar dados pessoais reais.

---

## 32. Banco de dados

Nomes de tabelas deverão seguir um padrão consistente.

Preferência inicial:

```text
snake_case
plural
```

Exemplos:

```text
leads
properties
conversations
messages
appointments
```

Colunas:

```text
lead_id
created_at
updated_at
max_price
```

---

## 33. IDs

Sempre que tecnicamente adequado, utilizar identificadores independentes da regra de negócio.

A decisão final sobre:

```text
UUID
integer identity
```

deverá ser tomada quando os modelos de persistência forem implementados.

Não introduzir complexidade apenas para antecipar uma necessidade inexistente.

---

## 34. Datas e horários

Internamente, preferir representação consistente.

Persistência deverá permitir tratamento adequado de timezone quando necessário.

Formatação para apresentação deve ser responsabilidade da camada apropriada.

---

## 35. Git

Antes de commit:

```bash
git status
```

Revisar arquivos incluídos.

Não versionar:

```text
.env
.idea/
.venv/
node_modules/
.next/
modelos locais
arquivos temporários
```

---

## 36. Branches

Para uma equipe pequena de Hackathon, preferir fluxo simples.

Branch principal:

```text
main
```

Branches de trabalho:

```text
feature/property-search
feature/lead-score
fix/health-endpoint
docs/architecture
```

Evitar estratégias complexas de branching sem necessidade.

---

## 37. Commits

Utilizar Conventional Commits de forma simples.

Tipos:

```text
feat
fix
test
docs
refactor
chore
```

Exemplos:

```text
feat: add lead persistence

feat: add property search endpoint

test: add health endpoint tests

docs: add architecture documentation

fix: handle missing property filters
```

Uma mensagem deve representar claramente a alteração.

---

## 38. Pull Requests

Quando utilizados, PRs deverão apresentar:

```text
objetivo
alterações principais
como testar
evidências
riscos ou pendências
```

Evitar PRs contendo múltiplas funcionalidades não relacionadas.

---

## 39. Dependências

Antes de adicionar uma biblioteca:

- verificar se já existe solução disponível;
- avaliar necessidade;
- avaliar manutenção;
- verificar compatibilidade;
- verificar licença quando relevante.

Adicionar a versão ou estratégia de gerenciamento definida pelo projeto quando a dependência for efetivamente incorporada.

---

## 40. Mudanças de arquitetura

Mudanças significativas devem primeiro atualizar ou discutir:

```text
docs/ARCHITECTURE.md
```

Código não deve estabelecer silenciosamente uma nova arquitetura diferente da documentada.

---

## 41. Mudanças de requisitos

Quando um requisito mudar:

```text
REQUIREMENTS.md
      ↓
Implementação
      ↓
Testes
```

A documentação e o comportamento devem permanecer coerentes.

---

## 42. Princípio de alteração mínima

Ao corrigir ou implementar uma tarefa:

> alterar apenas o necessário para cumprir o objetivo com qualidade.

Evitar modificar arquivos não relacionados apenas para melhorar estética ou estilo.

---

## 43. Definition of Done

Antes de considerar uma alteração concluída:

```text
[ ] requisito atendido
[ ] arquitetura respeitada
[ ] convenções respeitadas
[ ] testes adequados criados
[ ] testes executados
[ ] testes passando
[ ] aplicação continua funcional
[ ] documentação atualizada quando necessário
[ ] nenhum secret versionado
[ ] nenhuma alteração não relacionada incluída
```

---

## 44. Prioridade em caso de dúvida

Quando houver múltiplas alternativas igualmente válidas, priorizar:

```text
1. requisitos
2. arquitetura
3. segurança
4. testabilidade
5. simplicidade
6. clareza
7. desempenho
8. abstração
```

O projeto deve otimizar primeiro para uma POC funcional, confiável, compreensível e demonstrável.