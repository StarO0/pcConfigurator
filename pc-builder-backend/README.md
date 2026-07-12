# PC Builder Backend

Production-oriented backend конфигуратора ПК: FastAPI + PostgreSQL + Redis + Celery + детерминированная совместимость + сменяемые AI-провайдеры.

## Что уже работает

- регистрация, JWT access/refresh, ротация refresh token, выход с одного или всех устройств;
- подтверждение email, сброс и смена пароля, удаление/обезличивание аккаунта;
- роли `user/admin`, service tokens со scope, audit log;
- каталог, фильтры, пагинация, избранное, benchmarks и история цен;
- импорт предложений, EAN/MPN/SKU/fuzzy matching, CSV/JSON/API adapters;
- фоновые синхронизации магазинов и курсов NBP;
- пять целевых сборок через beam search: optimal, economy, upgrade-ready, AMD, Intel+NVIDIA;
- оптимизация по цене, доставке и количеству магазинов;
- расширенная проверка совместимости с точными причинами физических конфликтов в мм;
- мультиязычный AI/API-поток для UK, EN, PL и RU;
- bottleneck-анализ CPU/GPU сразу в ответе сборки;
- FPS, render-time и productivity estimates через импортируемую базу benchmarks;
- smart replacement groups: дешёвая альтернатива, разумный апгрейд, баланс;
- upsell-рекомендации мониторов, ИБП и периферии;
- приватные guest-сборки, сохранение, публикация, клонирование, корзина, ревизии;
- ручная замена компонентов с повторной проверкой всей сборки;
- сравнение сборок и JSON export;
- ценовые уведомления внутри приложения и через SMTP;
- AI providers: rules, OpenAI, Gemini, DeepSeek с fallback;
- Redis cache, rate limiting, idempotency, distributed locks;
- Alembic, PostgreSQL optimistic locking, Prometheus, Sentry, JSON logs;
- Docker Compose для разработки и production-образец с Nginx;
- OpenAPI и TypeScript-клиент.

## Ограничение, которое нельзя заполнить кодом заранее

В репозитории нет коммерческих фидов реальных магазинов и их ключей. Backend уже умеет принимать API/CSV/JSON-фиды и сопоставлять товары, но для каждого выбранного магазина нужны его разрешённый источник, формат и credentials. Демо-каталог и ссылки предназначены только для разработки.

## Локальный запуск без Docker

Требуется Python 3.12+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload
```

- Swagger: `http://localhost:8000/docs`
- API: `http://localhost:8000/api/v1`
- Metrics: `http://localhost:8000/metrics`

## Docker development

```bash
cp .env.example .env
docker compose up --build
```

Запускаются API, PostgreSQL, Redis, Celery worker и Celery Beat.

## Production example

```bash
cp .env.production.example .env.production
# заменить все GENERATE_/CHANGE значения, домены, SMTP и API keys
docker compose -f docker-compose.prod.yml up -d --build
```

Перед запуском положите TLS-файлы в:

```text
deploy/certs/fullchain.pem
deploy/certs/privkey.pem
```

Для Kubernetes/Cloud Run/ECS production compose служит архитектурным примером. Миграцию лучше выполнять отдельным release job до горизонтального запуска API.

## AI

По умолчанию:

```env
AI_PROVIDER=rules
AI_FALLBACK_PROVIDER=rules
```

Так проект полностью работает без внешнего ключа. Для OpenAI:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5-mini
```

AI выполняет только:

1. `parse_requirements` — текст пользователя в строгую схему;
2. `explain_build` — объяснение уже собранной конфигурации;
3. `explain_compatibility` — понятное описание ошибки.

Совместимость и выбор существующих товаров остаются в Python.

## Главные endpoints

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/products
GET    /api/v1/products/{id}
POST   /api/v1/builds/generate
GET    /api/v1/builds/{id}
GET    /api/v1/builds/{id}/analysis
GET    /api/v1/builds/{id}/replacement-options/{category}?sort=smart
PATCH  /api/v1/builds/{id}/components/{category}
POST   /api/v1/builds/{id}/save
POST   /api/v1/builds/compare
GET    /api/v1/builds/{id}/export
POST   /api/v1/price-alerts
GET    /api/v1/notifications
POST   /api/v1/admin/offers/import
POST   /api/v1/admin/stores/{id}/sync
GET    /api/v1/benchmarks/workloads
POST   /api/v1/benchmarks/admin/workloads
POST   /api/v1/benchmarks/admin/results/import
```

Полный контракт находится в `openapi.json`.

## Пример генерации

```bash
curl -X POST http://localhost:8000/api/v1/builds/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Тихий игровой ПК до 6000 PLN для 1440p","basket_mode":"balanced","language":"ru"}'
```

Каждая гостевая сборка получает отдельный `access_token`. Его нужно передавать как `X-Build-Token` при чтении или изменении приватной сборки.


## Пять продуктовых профилей

```text
optimal        точнее всего попадает в требования пользователя
economy        заметно дешевле при небольшой потере производительности
upgrade_ready  современная платформа, БП и корпус с запасом
amd            процессор AMD + видеокарта AMD
intel_nvidia   процессор Intel + видеокарта NVIDIA
```

Если пользователь задаёт жёсткое ограничение бренда, несовместимый брендовый профиль может быть пропущен. Это намеренно: backend не должен нарушать явное требование ради формального количества вариантов.

## Анализ производительности

`GET /api/v1/builds/{id}/analysis` возвращает:

- bottleneck CPU/GPU и до трёх совместимых рекомендаций;
- ожидаемый FPS для игровых workload;
- время экспорта/рендера для рабочих workload;
- оценку мощности и рекомендуемый БП;
- подходящие мониторы, ИБП и периферию.

Демо-значения benchmarks синтетические и нужны только для разработки интерфейса. Для коммерческого запуска импортируйте результаты из источников, на использование которых у проекта есть разрешение, через admin benchmark API. Оценки всегда помечаются confidence и disclaimer: это прогноз, а не гарантия конкретного FPS.

## Мультиязычность

`BuildRequirements.language` принимает `uk`, `en`, `pl`, `ru`. Rule-based parser сам определяет язык, а клиент может явно передать `language`. Названия пяти профилей, AI-объяснение, compatibility messages, bottleneck, smart replacements и upsell возвращаются на выбранном языке.

## Магазины и цены

См. [`docs/PARSER_ADAPTER.md`](docs/PARSER_ADAPTER.md). Generic adapters поддерживают:

- JSON GET/POST API;
- CSV;
- headers, params и JSON body;
- вложенные JSON paths;
- full snapshot deactivation;
- retry Celery;
- историю цены только при изменении.

## Миграции

```bash
alembic upgrade head
alembic revision --autogenerate -m "description"
alembic check
```

`AUTO_CREATE_TABLES=true` предназначен только для теста/быстрой локальной разработки. В production настройка обязана быть `false`.

## Тесты и качество

```bash
pytest -q --cov=app --cov-report=term-missing
ruff check .
ruff format --check .
```

CI проверяет Ruff, PostgreSQL migrations, `alembic check`, tests, coverage, актуальность OpenAPI и Docker build.

## Backup

```bash
export POSTGRES_USER=pcbuilder POSTGRES_DB=pcbuilder
./scripts/backup_postgres.sh
./scripts/restore_postgres.sh backups/file.dump
```

Резервные копии нужно дополнительно отправлять во внешнее хранилище и регулярно тестировать восстановление.

## Структура

```text
app/api/routes/          REST endpoints
app/core/                settings, security, logging, middleware
app/models/              SQLAlchemy models
app/schemas/             Pydantic contracts
app/services/            compatibility, generator, pricing, AI, parsers
app/workers/             Celery app and tasks
migrations/              Alembic revisions
docs/                    architecture and store adapter guide
examples/frontend-api.ts React/TypeScript client
```

Подробный поток: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
