# Catalogue sources and provenance

The v6 release does not include the former PCPartPicker-derived 67k metadata dataset or a
prebuilt SQLite database.

## Starter snapshot

`starter-snapshot-pl-2026-07-15.json` contains 332 separately identified x-kom listing
observations across 16 component and peripheral categories. Every entry has a product URL,
HTTPS image URL, positive PLN price, availability and observation timestamp. They are marked as
snapshot data and are not a promise of current availability.

## Open Icecat

New live records can be enriched through the public Open Icecat live endpoint. Icecat supplies
brand-authorized product content, including identity, specifications and image URLs. The project
stores source attribution and Icecat ID. Review the current Open Icecat terms before commercial
deployment: https://icecat.com/terms-and-conditions/

## Polish prices

Prices are separate offers collected from a confirmed public shop sitemap/feed/page. Each offer
stores its shop URL and fetched timestamp. Before enabling an automated source, the operator must
review its robots.txt and terms. An official merchant or affiliate feed remains the preferred
production source.
