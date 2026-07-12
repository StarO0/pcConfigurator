import logging
import time
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import AIUsage
from app.schemas.builds import BuildRequirements, CompatibilityIssue
from app.services.ai.base import AIProvider
from app.services.ai.deepseek_provider import DeepSeekProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_provider import OpenAIProvider
from app.services.ai.rules import RuleBasedAIProvider

logger = logging.getLogger(__name__)


def make_provider(name: str) -> AIProvider:
    factories = {
        "rules": RuleBasedAIProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "deepseek": DeepSeekProvider,
    }
    return factories[name]()


class AIService:
    def __init__(self) -> None:
        providers: list[AIProvider] = []
        for name in (settings.ai_provider, settings.ai_fallback_provider, "rules"):
            if any(item.name == name for item in providers):
                continue
            try:
                providers.append(make_provider(name))
            except Exception as exc:
                logger.warning("Failed to initialize AI provider %s: %s", name, exc)
        self.providers = providers or [RuleBasedAIProvider()]

    async def _run(
        self,
        operation: str,
        call,
        session: AsyncSession | None,
        user_id: UUID | None,
    ):
        last_error: Exception | None = None
        for provider in self.providers:
            started = time.perf_counter()
            succeeded = True
            error_type = None
            try:
                result = await call(provider)
            except Exception as exc:
                succeeded = False
                error_type = type(exc).__name__
                last_error = exc
                logger.warning(
                    "AI provider=%s operation=%s failed=%s",
                    provider.name,
                    operation,
                    error_type,
                )
            else:
                return result
            finally:
                if session is not None:
                    session.add(
                        AIUsage(
                            user_id=user_id,
                            provider=provider.name,
                            model=provider.model,
                            operation=operation,
                            latency_ms=int((time.perf_counter() - started) * 1000),
                            succeeded=succeeded,
                            error_type=error_type,
                        )
                    )
        if last_error is not None:
            raise last_error
        raise RuntimeError("No AI provider available")

    async def parse_requirements(
        self, prompt: str, session: AsyncSession | None = None, user_id: UUID | None = None
    ) -> BuildRequirements:
        return await self._run(
            "parse_requirements",
            lambda provider: provider.parse_requirements(prompt),
            session,
            user_id,
        )

    async def explain_build(
        self,
        requirements: BuildRequirements,
        profile: str,
        components: list[dict[str, Any]],
        total_price: float,
        session: AsyncSession | None = None,
        user_id: UUID | None = None,
    ) -> str:
        return await self._run(
            "explain_build",
            lambda provider: provider.explain_build(requirements, profile, components, total_price),
            session,
            user_id,
        )

    async def explain_compatibility(
        self,
        issues: list[CompatibilityIssue],
        session: AsyncSession | None = None,
        user_id: UUID | None = None,
    ) -> str:
        return await self._run(
            "explain_compatibility",
            lambda provider: provider.explain_compatibility(issues),
            session,
            user_id,
        )


ai_service = AIService()
