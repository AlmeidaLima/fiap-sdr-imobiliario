# Rastreabilidade de requisitos

Este documento relaciona os requisitos originais de [REQUIREMENTS.md](REQUIREMENTS.md) à implementação e aos testes existentes. As descrições abaixo são resumos fiéis; o texto normativo permanece no documento original.

Status usados:

- **ATENDIDO:** critérios essenciais comprovados pela implementação e testes.
- **PARCIALMENTE ATENDIDO:** existe entrega útil, mas parte explícita não foi implementada ou comprovada.
- **NÃO ATENDIDO:** a capacidade descrita não existe.
- **NÃO COMPROVADO:** não há evidência suficiente para concluir.

## Requisitos funcionais

| ID | Descrição original resumida | Status | Componente e endpoint | Testes | Limitações |
|---|---|---|---|---|---|
| RF001 | Iniciar atendimento, responder, identificar a conversa e recuperar histórico. | **ATENDIDO** | Chat; `POST /api/v1/conversations/turn`; `GET /api/v1/conversations/{conversation_id}/messages`. | `Chat.test.tsx`, `ChatPolling.test.tsx`, `test_conversation_api.py`. | Canal implementado: WEB. |
| RF002 | Identificar intenção `COMPRA`, `ALUGUEL`, `INVESTIMENTO` ou `INDEFINIDO` em linguagem natural. | **ATENDIDO** | `CommercialQualificationService`, estado da conversa e nodes. | `test_commercial_qualification_service.py`, `test_agent_nodes.py`. | Ambiguidades mantêm a qualificação em andamento. |
| RF003 | Coletar progressivamente dados relevantes sem repetir informação. | **PARCIALMENTE ATENDIDO** | `ConversationState`; serviços de identificação, qualificação e intenção de busca. | `test_conversation_flow.py`, `test_conversation_qualification_service.py`, `test_property_search_intent_service.py`. | Nome, intenção, região, orçamento, quartos e urgência são cobertos; nem todos os campos conceituais e de investimento têm fluxo próprio. |
| RF004 | Manter e atualizar contexto estruturado durante a conversa. | **ATENDIDO** | `Conversation.state`, `ConversationService`, persistência do turno. | `test_conversation_flow.py`, `test_conversation_persistence_api.py`, `test_conversation_state.py`. | Estado JSON validado e persistido. |
| RF005 | Persistir lead com ID único, atualização e recuperação. | **ATENDIDO** | `Lead`, `LeadRepository`, associação com `Conversation`. | `test_lead_model.py`, `test_lead_repository.py`, `test_conversation_persistence_api.py`. | Dados comerciais ficam no estado da conversa, sem duplicação no Lead. |
| RF006 | Persistir mensagens com ID, conversa, role, conteúdo e data. | **ATENDIDO** | `Message`, `MessageRepository`, API de histórico. | `test_message_model.py`, `test_message_repository.py`, `test_conversation_persistence_api.py`. | API pública expõe apenas `user` e `assistant`. |
| RF007 | Calcular Lead Score determinístico e classificação sem delegar a regra ao LLM. | **ATENDIDO** | `LeadScoreService`; score/classificação em `Conversation.state`. | `test_lead_score_service.py`, `test_commercial_qualification_service.py`, `test_agent_nodes.py`. | Regras por código, com limite de 100 pontos. |
| RF008 | Consultar base estruturada com filtros e sem inventar imóveis. | **ATENDIDO** | `GET /api/v1/properties`; repositories/services. | `test_properties_api.py`, `test_property_repository.py`, `test_property_service.py`. | Filtros refletem os dados efetivos do dataset. |
| RF009 | Importar CSV com limpeza, normalização, validação e contagem. | **ATENDIDO** | `scripts.import_curitiba_properties`; dataset versionado. | Validações de model/repository e execução reproduzível documentada. | Não há suíte dedicada abrangente do importador. |
| RF010 | Recomendar imóveis reais compatíveis com as preferências. | **ATENDIDO** | Busca da conversa, LangGraph e cards. | `test_conversation_search_flow.py`, `test_conversation_property_search_service.py`, `PropertySelection.test.tsx`. | Resultados são registros persistidos. |
| RF011 | Poder utilizar RAG textual com chunks, embeddings, pgvector e grounding. | **PARCIALMENTE ATENDIDO** | Documentos derivados de imóveis, `EmbeddingService`, busca semântica/híbrida. | `test_property_document_service.py`, `test_embedding_service.py`, `test_property_embedding_search.py`, `test_property_hybrid_search_service.py`. | Há recuperação vetorial de imóveis, mas não pipeline genérico de chunks para FAQs, bairros, políticas e financiamento. Como o requisito diz “poderá”, esse acervo é opcional; seus critérios específicos não estão integralmente atendidos. |
| RF012 | Realizar e registrar follow-up, evitar duplicidade e não contatar leads encerrados. | **PARCIALMENTE ATENDIDO** | `/api/v1/follow-ups`; worker; entrega WEB; follow-ups e attempts. | `test_lead_follow_up_service.py`, `test_lead_follow_up_delivery_service.py`, `test_lead_follow_up_job.py`, `test_run_lead_follow_up_worker.py`, `ChatPolling.test.tsx`. | Persistência, atomicidade e prevenção concorrente existem. A máquina de `Lead.status` (`FOLLOWUP_1`, `ENCERRADO` etc.) não existe; `COMPLETED` refere-se ao follow-up. |
| RF013 | Registrar agendamento relacionado ao lead, com tipo, data/hora, status e confirmação. | **PARCIALMENTE ATENDIDO** | `POST /api/v1/appointments`; `GET /api/v1/appointments/{id}`; Chat. | `test_appointment_service.py`, `test_appointment_flow_service.py`, `test_appointment_api.py`, `AppointmentFlow.test.tsx`. | Suporta `VISITA` e `REUNIAO`; não suporta o tipo conceitual `CONTATO`. |
| RF014 | Gerar resumo estruturado e fiel para o corretor. | **ATENDIDO** | `GET /api/v1/handoffs/{conversation_id}`; `LeadHandoffService`. | `test_lead_handoff_service.py`, `test_lead_handoff_api.py`, `LeadHandoffPanel.test.tsx`. | Retorna `READY` ou `NOT_READY` sem inventar dados. |
| RF015 | Dashboard mínimo com lista e detalhe de leads. | **ATENDIDO** | `/dashboard`; `GET /api/v1/dashboard/leads`; `GET /api/v1/dashboard/leads/{lead_id}`. | `test_dashboard_repository.py`, `test_dashboard_service.py`, `test_dashboard_api.py`, `Dashboard.test.tsx`, `dashboardService.test.ts`. | Somente leitura; não mostra follow-up. |
| RF016 | Preparar integração futura com WhatsApp pela Evolution API. | **NÃO ATENDIDO** | Nenhum adapter ou endpoint Evolution API. | Não há testes de WhatsApp. | Evolução futura; canal atual é WEB. |
| RF017 | Disponibilizar health check em `GET /health` com status e serviço. | **PARCIALMENTE ATENDIDO** | `GET /api/v1/health`, com o payload esperado. | `test_health.py`, `test_observability.py`. | A capacidade existe, mas o prefixo versionado difere do caminho literal original. |
| RF018 | Disponibilizar Swagger em `/docs`. | **ATENDIDO** | Documentação automática FastAPI em `/docs`. | Inicialização da aplicação e testes das rotas. | Disponível com o backend ativo. |

## Requisitos não funcionais

| ID | Descrição original resumida | Status | Implementação e evidência | Testes | Limitações |
|---|---|---|---|---|---|
| RNF001 | Execução padronizada por Docker Compose. | **ATENDIDO** | `compose.yaml`: PostgreSQL, backend, worker e frontend. | Smoke operacional; README. | Clone limpo requer migrations antes do conjunto completo. |
| RNF002 | Arquitetura testável com Pytest e regras determinísticas independentes do LLM. | **ATENDIDO** | Suites backend/frontend, services injetáveis e fallback. | `backend/tests/`, `frontend/__tests__/`. | Integrações de banco requerem PostgreSQL. |
| RNF003 | Não versionar credenciais e fornecer `.env.example`. | **ATENDIDO** | `.env.example`, `.gitignore`, configuração por ambiente. | `test_config.py` e auditoria Git. | Valores de exemplo são locais. |
| RNF004 | Separar Route, Service, Repository e Database; controlar acesso da IA. | **PARCIALMENTE ATENDIDO** | Camadas implementadas; nodes usam services controlados. | Testes por camada e de delegação. | Não existe camada física `tools/`; o controle equivalente ocorre em nodes/services, sem SQL pelo LLM. |
| RNF005 | Permitir clone e inicialização pelas instruções do README. | **ATENDIDO** | Bootstrap seguro, Windows e Docker documentados. | Comandos conferidos contra Compose, Dockerfiles e scripts. | Primeiro embedding exige rede; LLM é externo opcional. |
| RNF006 | Logs suficientes para diagnóstico sem expor secrets. | **ATENDIDO** | Request ID, formatter seguro e eventos da API/worker. | `test_observability.py`, `test_agent_nodes.py`, `test_conversation_api.py`, `test_run_lead_follow_up_worker.py`, `test_index_property_embeddings_script.py`. | Observabilidade local via stdout/stderr. |
| RNF007 | Endpoints sem IA rápidos, sem queries desnecessárias e tempo do LLM mensurável. | **PARCIALMENTE ATENDIDO** | Queries agregadas, lotes e durations nos logs HTTP/LLM/busca. | Testes de repositories, dashboard e observabilidade. | Sem SLA, benchmark formal ou relatório de carga, coerente com a POC. |
| RNF008 | Executar em containers e reduzir dependência da máquina local. | **ATENDIDO** | Dockerfiles e Compose. | Smoke Docker. | LLM externo opcional; primeiro embedding usa rede. |
| RNF009 | Código claro, com responsabilidades e sem abstrações prematuras. | **ATENDIDO** | Módulos por responsabilidade, services/repositories e testes. | Suite por componente e revisão arquitetural. | Classificação qualitativa baseada na organização atual. |
| RNF010 | Manter coerência, evitar invenção, assumir incerteza e usar dados recuperados. | **PARCIALMENTE ATENDIDO** | Estado persistido, propriedades canônicas, contexto controlado e fallback. | `test_llm_service.py`, `test_agent_nodes.py`, `test_sdr_graph.py`, testes de busca/seleção. | Sem avaliação ampla do modelo ou RAG documental genérico; não há camada física `tools/`. |

## Evidências por área

| Área | Código principal | Testes representativos |
|---|---|---|
| Conversa e memória | `app/api/routes/conversations.py`, `ConversationService`, `ConversationRepository`, `MessageRepository` | `test_conversation_api.py`, `test_conversation_persistence_api.py`, `test_message_repository.py` |
| Agente e qualificação | `app/agents/`, `CommercialQualificationService`, `LeadScoreService` | `test_agent_nodes.py`, `test_sdr_graph.py`, `test_lead_score_service.py` |
| Imóveis e vetores | rotas de properties e respectivos services/repositories | `test_properties_api.py`, `test_property_embedding_search.py`, `test_property_hybrid_search_service.py` |
| Agendamento e handoff | rotas e services de appointments/handoffs | `test_appointment_api.py`, `test_lead_handoff_api.py`, testes frontend dos painéis |
| Dashboard | rota, repository e service; `frontend/app/dashboard` | `test_dashboard_*.py`, `Dashboard.test.tsx` |
| Follow-up WEB | rotas, delivery service, job, worker e polling | `test_lead_follow_up_*.py`, `test_run_lead_follow_up_worker.py`, `ChatPolling.test.tsx` |
| Observabilidade | `app/core/observability.py`, eventos e worker | `test_observability.py`, testes de eventos internos e scripts |

## Justificativas de classificação

RF011 permanece parcial porque a implementação vetorial é específica para imóveis, enquanto os critérios originais descrevem documentos em chunks e conhecimento textual mais amplo. RF017 permanece parcial apenas pela divergência literal do caminho: o health funcional está sob o prefixo `/api/v1`. As classificações registram diferenças reais sem transformar componentes opcionais ou futuros em funcionalidades existentes.
