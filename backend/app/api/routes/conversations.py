import logging
from time import monotonic

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ApplicationException
from app.database.session import get_db
from app.database.conversation_repository import ConversationRepository
from app.database.lead_repository import LeadRepository
from app.database.message_repository import MessageRepository
from app.database.property_embedding_repository import (
    PropertyEmbeddingRepository,
)
from app.schemas.conversation import (
    ConversationState,
    ConversationMessageResponse,
    ConversationMessagesResponse,
    ConversationTurnRequest,
    ConversationTurnResponse,
)
from app.schemas.property import PropertySearchResponse
from app.services.conversation_persistence_service import (
    ConversationPersistenceService,
)
from app.services.conversation_property_search_service import (
    ConversationPropertySearchService,
)
from app.services.conversation_qualification_service import (
    ConversationQualificationService,
)
from app.services.embedding_service import EmbeddingService
from app.services.llm_client import LLMClient
from app.services.llm_service import LLMService
from app.services.property_hybrid_search_service import (
    PropertyHybridSearchService,
)
from app.services.property_selection_service import PropertySelectionService
from app.services.sdr_agent_service import SDRAgentService


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)

LOGGER = logging.getLogger(__name__)


@router.get(
    "/{conversation_id}/messages",
    response_model=ConversationMessagesResponse,
)
def get_conversation_messages(
        conversation_id: str,
        after_id: int | None = Query(default=None, ge=0),
        db: Session = Depends(get_db),
) -> ConversationMessagesResponse:
    conversation = ConversationRepository(db).find_by_conversation_id(
        conversation_id
    )
    if conversation is None:
        raise ApplicationException(
            detail="Conversa não encontrada.",
            status_code=404,
            error="conversation_not_found",
        )

    messages = MessageRepository(db).list_public_messages(
        conversation_id=conversation.id,
        after_id=after_id,
    )
    state = ConversationState(
        conversation_id=conversation_id,
        **(conversation.state or {}),
    )
    return ConversationMessagesResponse(
        messages=[
            ConversationMessageResponse(
                id=message.id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
            )
            for message in messages
        ],
        state=state,
        qualification=ConversationQualificationService().qualify(state),
    )


@router.post(
    "/turn",
    response_model=ConversationTurnResponse,
)
def process_conversation_turn(
        request: ConversationTurnRequest,
        db: Session = Depends(get_db),
) -> ConversationTurnResponse:
    started = monotonic()
    LOGGER.info(
        "conversation_turn_started",
        extra={"conversation_id": request.conversation_id},
    )

    # ============================================================
    # Repositories
    # ============================================================

    conversation_repository = ConversationRepository(db)
    message_repository = MessageRepository(db)
    lead_repository = LeadRepository(db)

    # ============================================================
    # Persistência da conversa
    # ============================================================

    persistence_service = ConversationPersistenceService(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        lead_repository=lead_repository,
    )

    conversation = persistence_service.get_or_create(
        conversation_id=request.conversation_id,
    )

    # ============================================================
    # Recupera o estado persistido
    # ============================================================

    persisted_state = conversation.state or {}

    conversation_state = ConversationState(
        conversation_id=request.conversation_id,
        **persisted_state,
    )

    if request.selected_property_id is not None:
        conversation_state = PropertySelectionService().select_property(
            state=conversation_state,
            property_id=request.selected_property_id,
        )

    # ============================================================
    # Persiste mensagem recebida do usuário
    # ============================================================

    user_message = persistence_service.save_message(
        conversation=conversation,
        role="user",
        content=request.message,
    )

    persisted_messages = persistence_service.get_messages(conversation)
    conversation_history = [
        {"role": message.role, "content": message.content}
        for message in persisted_messages[:-1]
        if message.role in {"user", "assistant"}
    ][-6:]

    # ============================================================
    # Factory da infraestrutura de busca
    #
    # A infraestrutura de embeddings é criada somente quando
    # o LangGraph encaminha um lead qualificado para a busca.
    # ============================================================

    def property_search_service_factory() -> ConversationPropertySearchService:
        embedding_service = EmbeddingService()

        property_embedding_repository = PropertyEmbeddingRepository(db)

        hybrid_search_service = PropertyHybridSearchService(
            embedding_service=embedding_service,
            repository=property_embedding_repository,
        )

        return ConversationPropertySearchService(
            hybrid_search_service=hybrid_search_service,
        )

    def llm_service_factory() -> LLMService:
        return LLMService(
            client=LLMClient(
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                timeout=settings.llm_timeout,
            )
        )

    # ============================================================
    # Agente SDR / LangGraph
    # ============================================================

    sdr_agent_service = SDRAgentService(
        property_search_service_factory=property_search_service_factory,
        llm_service_factory=llm_service_factory,
    )

    turn_result = sdr_agent_service.process_turn(
        conversation_state=conversation_state,
        message=request.message,
        limit=request.limit,
        conversation_history=conversation_history,
    )

    # ============================================================
    # Lead
    # ============================================================

    if turn_result.state.lead_name and conversation.lead_id is None:
        persistence_service.create_and_associate_lead(
            conversation=conversation,
            name=turn_result.state.lead_name,
        )

    # ============================================================
    # Atualiza estado persistido
    # ============================================================

    persistence_service.update_state(
        conversation=conversation,
        state=turn_result.state.model_dump(
            exclude={"conversation_id"},
            mode="json",
        ),
    )

    assistant_message = persistence_service.save_message(
        conversation=conversation,
        role="assistant",
        content=turn_result.response,
    )

    # ============================================================
    # Converte resultado da busca para schema HTTP
    # ============================================================

    properties = []

    for property_embedding, similarity_score in turn_result.properties:
        property_model = property_embedding.property

        properties.append(
            PropertySearchResponse(
                id=property_model.id,
                external_id=property_model.external_id,
                title=property_model.title,
                description=property_model.description,
                neighborhood=property_model.neighborhood,
                usable_area=property_model.usable_area,
                bedrooms=property_model.bedrooms,
                bathrooms=property_model.bathrooms,
                parking_spaces=property_model.parking_spaces,
                price=property_model.price,
                similarity_score=round(
                    similarity_score,
                    4,
                ),
            )
        )

    # ============================================================
    # Response
    # ============================================================

    response = ConversationTurnResponse(
        conversation_id=turn_result.state.conversation_id,
        user_message_id=user_message.id,
        assistant_message_id=assistant_message.id,
        user_message_created_at=user_message.created_at,
        assistant_message_created_at=assistant_message.created_at,
        response=turn_result.response,
        state=turn_result.state,
        qualification=turn_result.qualification,
        properties=properties,
    )
    LOGGER.info(
        "conversation_turn_completed",
        extra={
            "conversation_id": request.conversation_id,
            "qualified": turn_result.qualification.qualified,
            "property_count": len(properties),
            "duration_ms": round((monotonic() - started) * 1000),
        },
    )
    return response
