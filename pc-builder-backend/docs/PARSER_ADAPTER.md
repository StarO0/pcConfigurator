# Подключение магазина

В production предпочтителен официальный API, affiliate/XML/CSV/JSON-фид. Без API используйте Browser Collector, сохранённый HTML, JSON-LD/sitemap либо разрешённый XML/YML-фид. Серверный обход включайте только после проверки правил конкретного магазина.

## 1. Создать магазин

`POST /api/v1/admin/stores` под admin JWT:

```json
{
  "slug": "example-shop",
  "name": "Example Shop",
  "base_url": "https://shop.example",
  "country": "PL",
  "parser_type": "json",
  "parser_config": {
    "url": "https://shop.example/feed.json",
    "method": "GET",
    "timeout": 30,
    "headers": {"Authorization": "${EXAMPLE_SHOP_AUTHORIZATION}"},
    "items_path": "data.products",
    "fields": {
      "product_sku": "manufacturer_sku",
      "ean": "ean",
      "mpn": "mpn",
      "title": "name",
      "external_id": "id",
      "url": "product_url",
      "price": "prices.current",
      "shipping_price": "prices.shipping",
      "currency": "prices.currency",
      "in_stock": "availability.in_stock",
      "stock_quantity": "availability.quantity"
    }
  }
}
```

Для CSV используются те же логические имена полей плюс `delimiter`.

## 2. Секреты

Не храните ключи магазина в Git или базе. Generic adapter рекурсивно раскрывает значения вида `${ENV_NAME}` в URL, headers, params и JSON body. Передайте секрет через переменную окружения контейнера или secret manager.

## 3. Сопоставление

Порядок:

1. SKU/EAN/MPN;
2. точное название в той же категории;
3. fuzzy matching в той же категории и, если известен, бренде.

В PostgreSQL fuzzy shortlist использует `pg_trgm`, затем комбинируются `token_set_ratio` и `token_sort_ratio`. Автопубликация требует confidence не ниже 92%; более слабая запись остаётся в staging. При ручном подтверждении слабое совпадение создаёт отдельную модель, а не склеивается с похожим названием.

## 4. Keyless staging API

- `POST /api/v1/admin/harvester/browser-import` — JSON от расширения/локального инструмента;
- `POST /api/v1/admin/harvester/extract-preview` — проверить извлечение из HTML;
- `POST /api/v1/admin/harvester/html-import` — опубликовать или отправить HTML в staging;
- `POST /api/v1/admin/harvester/queue` — добавить разрешённые URL;
- `POST /api/v1/admin/harvester/queue/process/{store_id}` — обработать очередь;
- `GET /api/v1/admin/harvester/records` — review;
- `POST /api/v1/admin/harvester/records/{id}/approve` — принять запись.

## 5. Ручной push

Можно не давать backend доступ к магазину, а отправлять готовые данные через:

`POST /api/v1/admin/offers/import`

с `X-Service-Token`, имеющим scope `offers:write`.

## 6. Собственный adapter

Наследуйте `StoreParser` в `app/services/parsers/base.py`, верните список `OfferImportItem` и зарегистрируйте класс в `PARSERS` внутри `generic.py` либо вынесите registry в отдельный модуль.

Adapter обязан:

- использовать timeout;
- валидировать цену и URL через Pydantic;
- не логировать API secrets;
- возвращать стабильный `external_id`;
- отдавать полный snapshot, если исчезнувшие предложения нужно снять с продажи;
- бросать исключение при неполном/подозрительном фиде, чтобы Celery выполнил retry.
