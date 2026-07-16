# Release checks v6.1

Выполнено 15 июля 2026:

- `pytest -q`: **42 passed**;
- `ruff check app tests migrations`: passed;
- `ruff format --check app tests migrations`: passed;
- `npm run lint`: passed;
- `npm run build`: passed;
- Alembic PostgreSQL SQL generation through the single head `77e6121a6d20`: passed;
- safe CSV/XLSX/JSON/XML import preview: covered by automated tests;
- product comparison API and frontend comparison matrix: covered by tests/build;
- FastAPI validation errors, including custom Pydantic contexts: return serializable `422` responses;
- Docker frontend-to-backend proxy hosts are included in `TrustedHostMiddleware` configuration;
- bundled starter snapshot audit: 332 products / 332 active offers / 332 images across 16 categories and 86 brands;
- starter snapshot limitation: no EAN/MPN values and sparse normalized specs, so it is demo data rather than the final production catalog;
- Docker runtime: not available in the build environment; Compose files, health checks and local verification commands are supplied.

Run the environment-specific final runtime check on a machine with Docker:

```text
test-project-windows.bat
```

or:

```bash
./test-project.sh
```
