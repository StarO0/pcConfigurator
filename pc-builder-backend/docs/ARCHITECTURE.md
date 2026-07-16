# Архитектура PC Builder Backend

## Поток генерации

```text
React / mobile client
        |
        v
FastAPI -> rate limit / JWT / idempotency / audit
        |
        v
AIService.parse_requirements()
  rules | OpenAI | Gemini | DeepSeek
        |
        v
BuildGenerator (beam search: optimal/economy/upgrade/AMD/Intel+NVIDIA)
        |
        +--> PostgreSQL: products, offers, benchmarks
        +--> Pricing optimizer: цена + доставка + число магазинов
        +--> CompatibilityEngine: детерминированные правила
        |
        v
AIService.explain_build()
        |
        v
5 приватных сборок + отдельный guest token каждой сборки
```

ИИ не выбирает произвольные SKU и не решает совместимость. Он только переводит текст в `BuildRequirements` и объясняет уже проверенный результат.

## Хранение

- **PostgreSQL**: пользователи, сессии, каталог, предложения, история цен, сборки, ревизии, уведомления, аудит, AI usage.
- **Redis 0**: cache, rate limits, idempotency и distributed locks.
- **Redis 1**: Celery broker.
- **Redis 2**: Celery result backend.

## Фоновые очереди

- `parsers`: синхронизация фидов магазинов;
- `maintenance`: курсы валют, очистка истёкших данных;
- `notifications`: ценовые уведомления.

Celery Beat запускает периодические задачи. Только один экземпляр Beat должен работать одновременно.

## Безопасность доступа к сборкам

- Сборка гостя приватна и получает случайный `X-Build-Token`.
- После сохранения владельцем guest token удаляется.
- `private` доступна владельцу;
- `unlisted` доступна по URL;
- `public` предназначена для публичной выдачи.
- Изменения требуют `expected_version`, поэтому параллельная запись возвращает `409`.

## Масштабирование

API не хранит состояние процесса и масштабируется горизонтально. PostgreSQL и Redis должны быть общими. В production миграции запускаются один раз перед раскаткой новых API-инстансов. Worker можно масштабировать отдельно по очередям.


## Аналитический поток

```text
Build + ProductBenchmark + WorkloadProfile
        |
        +--> BottleneckService -> CPU/GPU balance + compatible upgrade candidates
        +--> PerformanceService -> FPS / render time / productivity estimate
        +--> RecommendationService -> smart replacement tabs + peripheral upsell
        |
        v
GET /builds/{id}/analysis (Redis cache by build version and language)
```

Версия сборки входит в cache key, поэтому после замены детали старый анализ не возвращается.
