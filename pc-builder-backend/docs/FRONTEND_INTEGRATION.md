# Next.js integration

Готовый клиент находится в `examples/frontend-api.ts` и использует:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Рекомендуемый поток страницы

1. `generateBuilds()` — получить до пяти доступных профилей сборки и сохранить guest tokens.
2. Показать карусель по `profile`.
3. `getAnalysis()` для активного слайда через TanStack Query.
4. При открытии детали вызвать `getReplacementOptions(..., {sort: "smart"})`.
5. Разбить варианты по `recommendation_group` на вкладки.
6. После `replaceComponent()` обновить Build в Zustand и инвалидировать query анализа.

## SEO

Страница генератора может быть SSR, но приватные результаты пользователя должны загружаться на клиенте и не кешироваться CDN. Публичные сборки через `/builds/public/{slug}` можно рендерить сервером и индексировать.

## Безопасность guest token

`X-Build-Token` не помещайте в URL. Клиент хранит его отдельно по build ID и передаёт только в заголовке. Для production предпочтительнее HttpOnly BFF-cookie в Next.js вместо постоянного хранения JWT в `localStorage`.
