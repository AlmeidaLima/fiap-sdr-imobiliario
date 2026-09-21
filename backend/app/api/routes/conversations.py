from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.conversation_repository import ConversationRepository
from app.database.lead_repository import LeadRepository
from app.database.message_repository import MessageRepository
from app.database.property_embedding_repository import (
    PropertyEmbeddingRepository,
)
from app.schemas.conversation import (
    ConversationState,
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
from app.services.embedding_service import EmbeddingService
from app.services.property_hybrid_search_service import (
    PropertyHybridSearchService,
)
from app.services.sdr_agent_service import SDRAgentService


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


@router.post(
    "/turn",
    response_model=ConversationTurnResponse,
)
def process_conversation_turn(
        request: ConversationTurnRequest,
        db: Session = Depends(get_db),
) -> ConversationTurnResponse:

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

    # ============================================================
    # Persiste mensagem recebida do usuário
    # ============================================================

    persistence_service.save_message(
        conversation=conversation,
        role="user",
        content=request.message,
    )

    # ============================================================
    # Infraestrutura da busca de imóveis
    # ============================================================

    embedding_service = EmbeddingService()

    property_embedding_repository = PropertyEmbeddingRepository(db)

    hybrid_search_service = PropertyHybridSearchService(
        embedding_service=embedding_service,
        repository=property_embedding_repository,
    )

    property_search_service = ConversationPropertySearchService(
        hybrid_search_service=hybrid_search_service,
    )

    # ============================================================
    # Agente SDR / LangGraph
    # ============================================================

    sdr_agent_service = SDRAgentService(
        property_search_service=property_search_service,
    )

    turn_result = sdr_agent_service.process_turn(
        conversation_state=conversation_state,
        message=request.message,
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

    return ConversationTurnResponse(
        conversation_id=turn_result.state.conversation_id,
        state=turn_result.state,
        qualification=turn_result.qualification,
        properties=properties,
    )