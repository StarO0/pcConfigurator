import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.builds import BuildRequirements
from app.services.ai.base import AIProvider
from app.services.i18n import language_name


class DeepSeekProvider(AIProvider):
    name = "deepseek"

    def __init__(self) -> None:
        if not settings.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required")
        self.model = settings.deepseek_model
        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key.get_secret_value(),
            base_url=settings.deepseek_base_url,
            timeout=settings.ai_timeout_seconds,
            max_retries=settings.ai_max_retries,
        )

    async def parse_requirements(self, prompt: str) -> BuildRequirements:
        response = await self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": f"Return only JSON matching this schema: {json.dumps(BuildRequirements.model_json_schema())}. Parse PC requirements only. Detect language as uk/en/pl/ru and include it in JSON.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return BuildRequirements.model_validate_json(content)

    async def explain_build(
        self,
        requirements: BuildRequirements,
        profile: str,
        components: list[dict[str, Any]],
        total_price: float,
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": f"Explain the supplied PC build briefly in {language_name(requirements.language)}. Do not invent facts.",
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "requirements": requirements.model_dump(),
                            "profile": profile,
                            "components": components,
                            "total_price": total_price,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        return (response.choices[0].message.content or "").strip()
