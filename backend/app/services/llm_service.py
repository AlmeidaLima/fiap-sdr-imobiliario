from app.services.llm_client import LLMClient


class LLMService:

    SYSTEM_PROMPT = (
        "Você é LIA, uma assistente SDR imobiliária. "
        "Responda de forma clara, objetiva e natural. "
        "Não invente informações sobre imóveis."
    )

    def __init__(
            self,
            client: LLMClient,
    ):
        self.client = client

    def generate_response(
            self,
            user_message: str,
    ) -> str:
        messages = [
            {
                "role": "system",
                "content": self.SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        return self.client.chat(
            messages=messages,
        )