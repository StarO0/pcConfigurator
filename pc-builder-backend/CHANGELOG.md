# Changelog

## 2.0.0 — product intelligence release

### Added

- multilingual request detection and localized responses for UK, EN, PL and RU;
- five business profiles: optimal, economy, upgrade-ready, AMD and Intel+NVIDIA;
- CPU/GPU bottleneck assessment in every build response;
- workload catalog and benchmark import API;
- FPS, render-time and productivity estimates with confidence/disclaimer;
- compatible bottleneck upgrade recommendations;
- smart replacement groups for cheaper alternatives and reasonable upgrades;
- detailed physical-clearance conflicts with missing millimetres/slots;
- monitor, UPS, keyboard, mouse and headset upsell recommendations;
- Redis-cached build analysis keyed by build version and language;
- Next.js-oriented TypeScript API client;
- workload profile Alembic migration and demo benchmark seed data;
- performance-engine and frontend-integration documentation.

### Changed

- build profiles now match product requirements instead of generic random variations;
- AI explanations preserve the language of the original request;
- compatibility messages are localizable and carry structured dimensions/details;
- replacement options default to smart product ranking;
- API version raised to 2.0.0.

### Notes

Demo benchmark values and store links are synthetic. Commercial deployment requires licensed benchmark data and authorized store feeds or affiliate APIs.
