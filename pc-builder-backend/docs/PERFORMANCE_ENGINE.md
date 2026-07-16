# Performance, bottleneck and recommendation engine

## Главное правило

Backend не обещает точный FPS «из воздуха». Он использует два уровня данных:

1. импортированные benchmark points конкретного CPU/GPU для workload;
2. fallback на нормализованный `performance_score`, если реального измерения нет.

Каждый результат содержит `confidence` и disclaimer.

## Workload profiles

Таблица `workload_profiles` описывает:

- тип: `game`, `render`, `productivity`;
- единицу: FPS, seconds, points;
- что важнее: CPU, GPU или hybrid;
- требование к RAM;
- базовое разрешение и preset;
- локализованные названия;
- ссылку на источник/методику.

Результаты компонентов хранятся в `product_benchmarks` и импортируются через:

```text
POST /api/v1/benchmarks/admin/results/import
```

## FPS

Для игры берутся:

- CPU ceiling для workload;
- GPU FPS для workload;
- коэффициент разрешения;
- штраф при нехватке RAM.

Итог ограничивается более слабой стороной. Это делает оценку понятной и не позволяет сильному CPU «дорисовать» FPS слабой видеокарте.

## Render time

Для CPU/GPU workload используется соответствующий результат. Для hybrid workload время объединяется через weighted throughput. Чем меньше seconds, тем лучше.

## Bottleneck

Bottleneck — относительная оценка баланса, а не универсальный физический процент. Она зависит от разрешения:

- 1080p сильнее нагружает CPU;
- 4K и 8K сильнее нагружают GPU.

Backend возвращает методологию `relative-score-v1`, severity и совместимые варианты замены, которые действительно уменьшают дисбаланс.

## Коммерческое использование

Не копируйте чужие benchmark-базы без лицензии. Храните источник и дату измерения, версионируйте методику, отделяйте разные presets и пересчитывайте результаты при обновлении формулы.
