import json
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.builds import BuildRequirements
from app.services.ai.base import AIProvider


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required")
        self.model = settings.gemini_model
        self.api_key = settings.gemini_api_key.get_secret_value()

    async def _generate(self, text: str, *, json_mode: bool = False) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        )
        generation_config: dict[str, Any] = {"temperature": 0.1, "maxOutputTokens": 700}
        if json_mode:
            generation_config["responseMimeType"] = "application/json"
            generation_config["responseJsonSchema"] = BuildRequirements.model_json_schema()
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": text}]}],
                    "generationConfig": generation_config,
                },
            )
            response.raise_for_status()
            data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    async def parse_requirements(self, prompt: str) -> BuildRequirements:
        content = await self._generate(
            "Parse only PC hardware requirements. Never select components. Default PLN/6000. User: "
            + prompt,
            json_mode=True,
        )
        return BuildRequirements.model_validate_json(content)

    async def explain_build(
        self,
        requirements: BuildRequirements,
        profile: str,
        components: list[dict[str, Any]],
        total_price: float,
    ) -> str:
        return (
            await self._generate(
                "Explain this PC build briefly in Russian using only supplied facts: "
                + json.dumps(
                    {
                        "requirements": requirements.model_dump(),
                        "profile": profile,
                        "components": components,
                        "total_price": total_price,
                    },
                    ensure_ascii=False,
                )
            )
        ).strip()
