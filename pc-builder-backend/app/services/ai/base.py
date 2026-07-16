from abc import ABC, abstractmethod
from typing import Any

from app.schemas.builds import BuildRequirements, CompatibilityIssue


class AIProvider(ABC):
    name = "base"
    model = "base"

    @abstractmethod
    async def parse_requirements(self, prompt: str) -> BuildRequirements:
        raise NotImplementedError

    @abstractmethod
    async def explain_build(
        self,
        requirements: BuildRequirements,
        profile: str,
        components: list[dict[str, Any]],
        total_price: float,
    ) -> str:
        raise NotImplementedError

    async def explain_compatibility(
        self,
        issues: list[CompatibilityIssue],
    ) -> str:
        return " ".join(issue.message for issue in issues)
