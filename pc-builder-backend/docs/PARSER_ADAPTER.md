# Подключение магазина

В production предпочтителен официальный API, affiliate/XML/CSV/JSON-фид. HTML scraping стоит использовать только после проверки правил конкретного магазина.

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

1. `product_sku`;
2. EAN;
3. MPN;
4. fuzzy matching нормализованного названия.

В PostgreSQL fuzzy shortlist использует `pg_trgm`, после чего применяется `token_set_ratio`. Низкая уверенность не создаёт связь автоматически: предложение попадает в `unmatched`.

## 4. Ручной push

Можно не давать backend доступ к магазину, а отправлять готовые данные через:

`POST /api/v1/admin/offers/import`

с `X-Service-Token`, имеющим scope `offers:write`.

## 5. Собственный adapter

Наследуйте `StoreParser` в `app/services/parsers/base.py`, верните список `OfferImportItem` и зарегистрируйте класс в `PARSERS` внутри `generic.py` либо вынесите registry в отдельный модуль.

Adapter обязан:

- использовать timeout;
- валидировать цену и URL через Pydantic;
- не логировать API secrets;
- возвращать стабильный `external_id`;
- отдавать полный snapshot, если исчезнувшие предложения нужно снять с продажи;
- бросать исключение при неполном/подозрительном фиде, чтобы Celery выполнил retry.
