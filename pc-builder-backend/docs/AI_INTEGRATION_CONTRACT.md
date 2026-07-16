# AI integration contract

The AI layer is intentionally replaceable. Product selection, compatibility and pricing remain deterministic services.

## Provider interface

Every provider implements `AIProvider`:

```python
async def parse_requirements(prompt: str) -> BuildRequirements
async def explain_build(requirements, profile, components, total_price) -> str
async def explain_compatibility(issues) -> str
```

Available provider adapters:

- `rules` — local fallback with no key;
- `openai`;
- `gemini`;
- `deepseek`.

Select providers with:

```env
AI_PROVIDER=rules
AI_FALLBACK_PROVIDER=rules
```

The service tries the primary provider, then the fallback, then the local rules provider. Calls are recorded in `ai_usage` with latency and failure metadata.

## Required output contract

`parse_requirements` must return the validated `BuildRequirements` schema. The provider must never return product IDs or decide whether components are compatible. It only converts user intent into structured requirements.

The deterministic generator then:

1. loads active products and offers;
2. applies budget and user constraints;
3. validates compatibility;
4. optimizes store baskets and delivery;
5. persists builds;
6. asks the provider only for a human-readable explanation.

## Recommended final AI workflow

1. Add a dedicated chat endpoint supporting conversation state and explicit clarification questions.
2. Store a compact requirement draft, not raw hidden chain-of-thought.
3. Validate every provider response through Pydantic.
4. Add timeout, retry and cost/token limits per user.
5. Build an evaluation set covering Polish, Russian, Ukrainian and English prompts.
6. Compare parsed requirements and final builds against deterministic expected results.
7. Keep a rules fallback so the site remains usable when the model provider is unavailable.
