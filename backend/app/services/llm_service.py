import json

from app.schemas.conversation import (
    ConversationQualification,
    ConversationState,
)
from app.services.llm_client import LLMClient


class LLMService:

    SYSTEM_PROMPT = (
        "Você é LIA, uma assistente SDR imobiliária. "
        "Responda de forma clara, objetiva e natural. "
        "A qualificação e a próxima pergunta são definidas pela aplicação; "
        "não altere essas decisões. "
        "Use o histórico somente para continuidade conversacional, nunca como "
        "fonte factual sobre imóveis. "
        "Sobre imóveis, use exclusivamente os dados presentes em "
        "imoveis_recuperados. Não invente, complete ou infira imóveis, preços, "
        "endereços, características ou disponibilidade. Quando um atributo não "
        "estiver presente, informe que ele não foi disponibilizado."
    )

    def __init__(
            self,
            client: LLMClient,
    ):
        self.client = client

    def generate_response(
            self,
            user_message: str,
            conversation_state: ConversationState,
            qualification: ConversationQualification,
            conversation_history: list[dict[str, str]] | None = None,
            properties_context: list[dict] | None = None,
    ) -> str:
        history = (conversation_history or [])[-6:]
        properties = properties_context or []

        controlled_context = {
            "mensagem_atual": user_message,
            "estado_factual": conversation_state.model_dump(
                exclude={"conversation_id"},
                exclude_none=True,
                mode="json",
            ),
            "qualificacao": qualification.model_dump(mode="json"),
            "imoveis_recuperados": properties,
        }

        messages = [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT,
            },
        ]

        messages.extend(history)

        messages.append(
            {
                "role": "user",
                "content": (
                    "Gere a resposta ao lead usando somente o contexto "
                    "controlado abaixo. Se a conversa não estiver qualificada, "
                    "faça a próxima pergunta indicada, com formulação natural. "
                    "Se estiver qualificada, apresente somente os imóveis "
                    "recuperados. Se a lista estiver vazia, informe que nenhum "
                    "imóvel compatível foi encontrado.\n\n"
                    + json.dumps(
                        controlled_context,
                        ensure_ascii=False,
                    )
                ),
            }
        )

        return self.client.chat(
            messages=messages,
        )
