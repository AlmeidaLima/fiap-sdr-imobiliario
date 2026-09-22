from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.conversation_repository import (
    ConversationRepository,
)
from app.database.lead_repository import (
    LeadRepository,
)
from app.database.message_repository import (
    MessageRepository,
)
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
from app.services.conversation_persistence_service import (
    ConversationPersistenceService,
)
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
    - recupera ou cria a conversa pelo conversation_id;
    - recupera o estado persistido no PostgreSQL;
    - persiste a mensagem enviada pelo usuário;
    - interpreta a nova mensagem;
    - identifica o nome do lead;
    - cria e associa o lead quando necessário;
    - acumula os critérios;
    - avalia a qualificação;
    - quando qualificado, executa busca híbrida;
    - persiste o novo estado;
    - retorna estado, qualificação e imóveis.
    """

    conversation_repository = ConversationRepository(db)
    message_repository = MessageRepository(db)
    lead_repository = LeadRepository(db)

    persistence_service = ConversationPersistenceService(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        lead_repository=lead_repository,
    )

    persisted_conversation = persistence_service.get_or_create(
        request.conversation_id
    )

    state = ConversationState(
        conversation_id=request.conversation_id,
        **persisted_conversation.state,
    )

    persistence_service.save_message(
        conversation=persisted_conversation,
        role="user",
        content=request.message,
    )

    # ============================================================
    # PROCESSAMENTO E QUALIFICAÇÃO
    #
    # Neste momento ainda não criamos o EmbeddingService.
    # A interpretação da mensagem e a qualificação não precisam
    # carregar o modelo de embeddings.
    # ============================================================

    conversation_service = ConversationService()

    result = conversation_service.process_turn(
        state=state,
        message=request.message,
    )

    # ============================================================
    # BUSCA DE IMÓVEIS
    #
    # O modelo de embeddings é carregado somente quando o lead
    # possui os critérios mínimos necessários para a busca.
    # Isso evita inicializar o SentenceTransformer nos primeiros
    # turnos da conversa.
    # ============================================================

    if result.qualification.qualified:
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

        result.properties = property_search_service.search(
            state=result.state,
            limit=request.limit,
        )

    # ============================================================
    # LEAD
    # ============================================================

    if (
            result.state.lead_name is not None
            and persisted_conversation.lead_id is None
    ):
        persistence_service.create_and_associate_lead(
            conversation=persisted_conversation,
            name=result.state.lead_name,
        )

    # ============================================================
    # PERSISTÊNCIA DO ESTADO
    # ============================================================

    state_data = result.state.model_dump(
        exclude={
            "conversation_id",
        },
        mode="json",
    )

    persistence_service.update_state(
        conversation=persisted_conversation,
        state=state_data,
    )

    # ============================================================
    # MAPEAMENTO DOS IMÓVEIS PARA A RESPOSTA DA API
    # ============================================================

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