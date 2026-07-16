# Project completion status — v6.1

## Closed technical blocks

- PostgreSQL runtime and Alembic migrations.
- Dockerized frontend, API, Redis, worker and scheduler.
- Product, offer, price-history, user, build, favourite, notification and audit schemas.
- Catalogue search, filtering, product comparison and price-history UI.
- JSON/CSV/XLSX/XML import preparation with duplicate matching and staging.
- Authentication, token rotation, account sessions and admin role controls.
- Manual and generated builds, compatibility, replacements, revisions, public links and export.
- Celery schedules for store sync, currencies, alerts and cleanup.
- Admin API and frontend panels for data operations.
- Production frontend build without external Google Fonts.
- Same-origin frontend proxy and Docker trusted-host configuration.
- Validation errors consistently return HTTP 422 rather than failing with HTTP 500.

## Deliberately remaining

### 1. Product data

A production catalogue still needs a legal, stable source containing identifiers, images and category-specific specifications. Polish offers then need to be matched by EAN/GTIN, MPN or exact model. The import and matching infrastructure is already present.

Minimum required specs for core PC categories:

- CPU: socket, cores, threads, peak power.
- Motherboard: socket, RAM type, form factor, slots and connectors.
- GPU: length, peak power, VRAM and GPU vendor.
- RAM: DDR type, capacity, speed and module count.
- Storage: interface, form factor, capacity and PCIe generation.
- PSU: wattage, connectors and form factor.
- Case: supported motherboard formats, GPU length and cooler height.
- Cooler: supported sockets, height and cooling capacity.

### 2. Final AI layer

The backend already exposes a provider contract and deterministic build engine. Remaining AI work is product work rather than architecture work: final prompt design, clarification dialogue, model choice, evaluation dataset, cost limits and moderation. Compatibility must remain deterministic and must not be delegated to an LLM.

## Release gate before public deployment

- Replace all local secrets.
- Run `test-project.sh` against Docker Desktop.
- Connect real SMTP and monitoring.
- Review store terms, robots policy and affiliate/feed agreements.
- Import normalized products with required specifications.
- Run load tests with the target catalogue size.
- Configure backups and restore drills on the deployment platform.
