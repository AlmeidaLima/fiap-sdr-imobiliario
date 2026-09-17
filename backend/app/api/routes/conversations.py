from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.property_embedding_repository import (
    PropertyEmbeddingRepository,
)
from app.database.session import get_db
from app.schemas.conversation import (
    ConversationState,
    ConversationTurnRequest,
    ConversationTurnResponse,
)
from app.schemas.property import PropertySearchResponse
from app.services.conversation_property_search_service import (
    ConversationPropertySearchService,
)
from app.services.conversation_service import (
    ConversationService,
)
from app.services.embedding_service import (
    EmbeddingService,
)
from app.services.property_hybrid_search_service import (
    PropertyHybridSearchService,
)


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
    """
    Processa um turno da conversa do SDR imobiliário.

    Fluxo:
    - recupera o estado enviado pelo cliente;
    - interpreta a nova mensagem;
    - acumula os critérios;
    - avalia a qualificação;
    - quando qualificado, executa busca híbrida;
    - retorna estado, qualificação e imóveis.
    """

    state = request.state

    if state is None:
        state = ConversationState(
            conversation_id=request.conversation_id,
        )

    repository = PropertyEmbeddingRepository(
        db
    )

    embedding_service = EmbeddingService()

    hybrid_search_service = (
        PropertyHybridSearchService(
            embedding_service=embedding_service,
            repository=repository,
        )
    )

    property_search_service = (
        ConversationPropertySearchService(
            hybrid_search_service=(
                hybrid_search_service
            ),
        )
    )

    conversation_service = ConversationService(
        property_search_service=(
            property_search_service
        ),
    )

    result = conversation_service.process_turn(
        state=state,
        message=request.message,
    )

    properties = []

    for property_embedding, similarity_score in (
            result.properties
    ):
        property_data = property_embedding.property

        properties.append(
            PropertySearchResponse(
                id=property_data.id,
                external_id=(
                    property_data.external_id
                ),
                title=property_data.title,
                description=property_data.description,
                neighborhood=(
                    property_data.neighborhood
                ),
                usable_area=(
                    property_data.usable_area
                ),
                bedrooms=property_data.bedrooms,
                bathrooms=property_data.bathrooms,
                parking_spaces=(
                    property_data.parking_spaces
                ),
                price=property_data.price,
                similarity_score=round(
                    similarity_score,
                    4,
                ),
            )
        )

    return ConversationTurnResponse(
        conversation_id=(
            result.state.conversation_id
        ),
        state=result.state,
        qualification=result.qualification,
        properties=properties,
    )