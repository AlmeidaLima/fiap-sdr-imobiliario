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

        if not qualification.qualified:
            search_status = "NAO_EXECUTADA"
            search_instruction = (
                "A busca de imóveis ainda não foi executada. Faça somente "
                "a próxima pergunta indicada pela qualificação, podendo "
                "contextualizar brevemente os dados já informados. Nunca diga "
                "que não encontrou imóveis ou que a busca retornou zero "
                "resultados."
            )
        elif not properties:
            search_status = "EXECUTADA_SEM_RESULTADOS"
            search_instruction = (
                "A busca de imóveis foi executada e nenhum imóvel compatível "
                "foi recuperado. Informe a ausência de resultados sem inventar "
                "imóveis."
            )
        else:
            search_status = "EXECUTADA_COM_RESULTADOS"
            search_instruction = (
                "A busca de imóveis foi executada. Apresente e contextualize "
                "somente os imóveis presentes em imoveis_recuperados, sem "
                "inventar imóveis, preços ou atributos."
            )

        controlled_context = {
            "mensagem_atual": user_message,
            "estado_factual": conversation_state.model_dump(
                exclude={"conversation_id"},
                exclude_none=True,
                mode="json",
            ),
            "qualificacao": qualification.model_dump(mode="json"),
            "situacao_busca": search_status,
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
                    "controlado abaixo. Siga exclusivamente a regra correspondente "
                    "a situacao_busca: "
                    + search_instruction
                    + "\n\n"
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
