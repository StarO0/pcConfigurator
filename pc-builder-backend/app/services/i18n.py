from __future__ import annotations

import re
from typing import Any

SUPPORTED_LANGUAGES = {"uk", "en", "pl", "ru"}

LANGUAGE_NAMES = {
    "uk": "Ukrainian",
    "en": "English",
    "pl": "Polish",
    "ru": "Russian",
}

PROFILE_TITLES = {
    "optimal": {
        "uk": "Оптимальний вибір",
        "en": "Optimal choice",
        "pl": "Optymalny wybór",
        "ru": "Оптимальный выбор",
    },
    "economy": {
        "uk": "Максимальна економія",
        "en": "Maximum savings",
        "pl": "Maksymalna oszczędność",
        "ru": "Максимальная экономия",
    },
    "upgrade_ready": {
        "uk": "Збірка на виріст",
        "en": "Upgrade-ready build",
        "pl": "Zestaw gotowy na rozbudowę",
        "ru": "Сборка на вырост",
    },
    "amd": {
        "uk": "Збірка AMD",
        "en": "AMD build",
        "pl": "Zestaw AMD",
        "ru": "Сборка AMD",
    },
    "intel_nvidia": {
        "uk": "Збірка Intel + NVIDIA",
        "en": "Intel + NVIDIA build",
        "pl": "Zestaw Intel + NVIDIA",
        "ru": "Сборка Intel + NVIDIA",
    },
}

TEXTS: dict[str, dict[str, str]] = {
    "build_explanation": {
        "uk": (
            "Цей варіант оптимізовано під профіль «{profile}» і задачі: {purposes}. "
            "Зв'язка {cpu} та {gpu} пройшла перевірку сумісності, живлення, охолодження "
            "і фізичних габаритів. Підсумкова ціна з доставкою: {price:.2f} {currency}."
        ),
        "en": (
            "This option is optimized for the “{profile}” profile and these workloads: {purposes}. "
            "The {cpu} and {gpu} pairing passed compatibility, power, cooling, and physical-clearance "
            "checks. Total price including delivery: {price:.2f} {currency}."
        ),
        "pl": (
            "Ten wariant zoptymalizowano pod profil „{profile}” i zadania: {purposes}. "
            "Połączenie {cpu} i {gpu} przeszło kontrolę zgodności, zasilania, chłodzenia "
            "oraz wymiarów fizycznych. Cena końcowa z dostawą: {price:.2f} {currency}."
        ),
        "ru": (
            "Этот вариант оптимизирован под профиль «{profile}» и задачи: {purposes}. "
            "Связка {cpu} и {gpu} прошла проверку совместимости, питания, охлаждения "
            "и физических габаритов. Итоговая цена с доставкой: {price:.2f} {currency}."
        ),
    },
    "bottleneck_balanced": {
        "uk": "Зв'язка CPU і GPU добре збалансована для {resolution}.",
        "en": "The CPU and GPU are well balanced for {resolution}.",
        "pl": "Procesor i karta graficzna są dobrze zbalansowane dla {resolution}.",
        "ru": "Связка CPU и GPU хорошо сбалансирована для {resolution}.",
    },
    "bottleneck_cpu": {
        "uk": "Процесор може обмежувати відеокарту приблизно на {percent}% у {resolution}.",
        "en": "The CPU may limit the GPU by roughly {percent}% at {resolution}.",
        "pl": "Procesor może ograniczać kartę graficzną o około {percent}% w {resolution}.",
        "ru": "Процессор может ограничивать видеокарту примерно на {percent}% в {resolution}.",
    },
    "bottleneck_gpu": {
        "uk": "Відеокарта є головним обмеженням продуктивності приблизно на {percent}% у {resolution}.",
        "en": "The GPU is the main performance limit by roughly {percent}% at {resolution}.",
        "pl": "Karta graficzna jest głównym ograniczeniem wydajności o około {percent}% w {resolution}.",
        "ru": "Видеокарта является главным ограничением производительности примерно на {percent}% в {resolution}.",
    },
    "replacement_cheaper": {
        "uk": "Дешевша альтернатива без суттєвої втрати продуктивності.",
        "en": "A cheaper alternative with no major performance loss.",
        "pl": "Tańsza alternatywa bez dużej utraty wydajności.",
        "ru": "Более дешёвая альтернатива без заметной потери производительности.",
    },
    "replacement_upgrade": {
        "uk": "Розумний апгрейд: помітний приріст за помірну доплату.",
        "en": "Smart upgrade: a meaningful gain for a moderate extra cost.",
        "pl": "Rozsądna modernizacja: wyraźny wzrost za umiarkowaną dopłatę.",
        "ru": "Разумный апгрейд: заметный прирост за умеренную доплату.",
    },
    "replacement_balanced": {
        "uk": "Сумісний збалансований варіант.",
        "en": "A compatible balanced option.",
        "pl": "Zgodny, zbalansowany wariant.",
        "ru": "Совместимый сбалансированный вариант.",
    },
    "upsell_monitor": {
        "uk": "Монітор відповідає роздільній здатності та частоті кадрів цієї збірки.",
        "en": "This monitor matches the build’s target resolution and frame rate.",
        "pl": "Monitor pasuje do docelowej rozdzielczości i liczby klatek zestawu.",
        "ru": "Монитор соответствует целевому разрешению и частоте кадров этой сборки.",
    },
    "upsell_ups": {
        "uk": "ДБЖ має достатній запас потужності для захисту цієї системи.",
        "en": "The UPS has enough capacity to protect this system.",
        "pl": "UPS ma wystarczający zapas mocy do ochrony tego zestawu.",
        "ru": "ИБП имеет достаточный запас мощности для защиты этой системы.",
    },
    "upsell_peripheral": {
        "uk": "Практичне доповнення до готового робочого місця.",
        "en": "A practical addition to complete the setup.",
        "pl": "Praktyczne uzupełnienie kompletnego stanowiska.",
        "ru": "Практичное дополнение к готовому рабочему месту.",
    },
}

COMPATIBILITY_MESSAGES: dict[str, dict[str, str]] = {
    "cpu_socket_mismatch": {
        "uk": "Сокети процесора та материнської плати не збігаються.",
        "en": "The CPU and motherboard sockets do not match.",
        "pl": "Gniazda procesora i płyty głównej nie są zgodne.",
        "ru": "Сокеты процессора и материнской платы не совпадают.",
    },
    "cpu_not_in_support_list": {
        "uk": "Материнська плата не заявляє підтримку цього процесора.",
        "en": "The motherboard does not list this CPU as supported.",
        "pl": "Płyta główna nie deklaruje obsługi tego procesora.",
        "ru": "Материнская плата не заявляет поддержку этого процессора.",
    },
    "bios_update_required": {
        "uk": "Для цього процесора потрібне оновлення BIOS: мінімум {required}, зараз {current}.",
        "en": "This CPU requires a BIOS update: at least {required}, current {current}.",
        "pl": "Ten procesor wymaga aktualizacji BIOS-u: minimum {required}, obecnie {current}.",
        "ru": "Для этого процессора требуется обновление BIOS: минимум {required}, сейчас {current}.",
    },
    "vrm_insufficient": {
        "uk": "VRM плати розрахований приблизно на {board_limit_w} Вт, а CPU може споживати {cpu_power_w} Вт.",
        "en": "The board VRM is rated for roughly {board_limit_w} W, while the CPU may draw {cpu_power_w} W.",
        "pl": "Sekcja zasilania płyty jest przewidziana na około {board_limit_w} W, a CPU może pobierać {cpu_power_w} W.",
        "ru": "VRM платы рассчитан примерно на {board_limit_w} Вт, а CPU может потреблять {cpu_power_w} Вт.",
    },
    "cpu_overclocking_unavailable": {
        "uk": "Розгін CPU на цій платі недоступний.",
        "en": "CPU overclocking is unavailable on this motherboard.",
        "pl": "Podkręcanie procesora nie jest dostępne na tej płycie.",
        "ru": "Разгон CPU на этой плате недоступен.",
    },
    "ram_type_mismatch": {
        "uk": "Тип пам'яті не підтримується материнською платою.",
        "en": "The memory type is not supported by the motherboard.",
        "pl": "Typ pamięci nie jest obsługiwany przez płytę główną.",
        "ru": "Тип памяти не поддерживается материнской платой.",
    },
    "not_enough_ram_slots": {
        "uk": "Потрібно {modules} модулів RAM, але плата має лише {slots} слотів.",
        "en": "The kit needs {modules} RAM slots, but the board has only {slots}.",
        "pl": "Zestaw wymaga {modules} slotów RAM, a płyta ma tylko {slots}.",
        "ru": "Комплекту нужно {modules} слотов RAM, но у платы только {slots}.",
    },
    "ram_capacity_too_high": {
        "uk": "Обсяг RAM перевищує максимальну місткість материнської плати.",
        "en": "The RAM capacity exceeds the motherboard maximum.",
        "pl": "Pojemność RAM przekracza limit płyty głównej.",
        "ru": "Объём RAM превышает максимум материнской платы.",
    },
    "ram_speed_downclock": {
        "uk": "RAM на {ram_mhz} МГц працюватиме максимум на {board_mhz} МГц.",
        "en": "The {ram_mhz} MHz RAM will run at up to {board_mhz} MHz.",
        "pl": "Pamięć {ram_mhz} MHz będzie pracować maksymalnie z {board_mhz} MHz.",
        "ru": "RAM на {ram_mhz} МГц будет работать максимум на {board_mhz} МГц.",
    },
    "ecc_not_supported": {
        "uk": "ECC-пам'ять не підтримується цією платою.",
        "en": "ECC memory is not supported by this motherboard.",
        "pl": "Pamięć ECC nie jest obsługiwana przez tę płytę.",
        "ru": "ECC-память не поддерживается этой платой.",
    },
    "ram_cooler_clearance": {
        "uk": "Модулі RAM вищі за допустимий зазор кулера на {difference_mm} мм.",
        "en": "The RAM modules exceed the cooler clearance by {difference_mm} mm.",
        "pl": "Moduły RAM przekraczają prześwit chłodzenia o {difference_mm} mm.",
        "ru": "Модули RAM выше допустимого зазора кулера на {difference_mm} мм.",
    },
    "cooler_socket_mismatch": {
        "uk": "Кулер не підтримує сокет процесора.",
        "en": "The cooler does not support the CPU socket.",
        "pl": "Chłodzenie nie obsługuje gniazda procesora.",
        "ru": "Кулер не поддерживает сокет процессора.",
    },
    "cooler_capacity_low": {
        "uk": "Кулер відводить близько {capacity_w} Вт, а CPU потребує до {required_w} Вт.",
        "en": "The cooler handles about {capacity_w} W, while the CPU may require {required_w} W.",
        "pl": "Chłodzenie odprowadza około {capacity_w} W, a CPU może wymagać {required_w} W.",
        "ru": "Кулер отводит около {capacity_w} Вт, а CPU может требовать до {required_w} Вт.",
    },
    "cooler_low_headroom": {
        "uk": "Запас охолодження невеликий; під навантаженням система може бути гучною.",
        "en": "Cooling headroom is small; the system may become noisy under load.",
        "pl": "Zapas chłodzenia jest mały; pod obciążeniem zestaw może być głośny.",
        "ru": "Запас охлаждения небольшой; под нагрузкой система может быть шумной.",
    },
    "radiator_not_supported": {
        "uk": "Корпус не підтримує радіатор розміром {radiator_mm} мм.",
        "en": "The case does not support a {radiator_mm} mm radiator.",
        "pl": "Obudowa nie obsługuje chłodnicy {radiator_mm} mm.",
        "ru": "Корпус не поддерживает радиатор размером {radiator_mm} мм.",
    },
    "motherboard_case_mismatch": {
        "uk": "Форм-фактор материнської плати не підтримується корпусом.",
        "en": "The motherboard form factor is not supported by the case.",
        "pl": "Format płyty głównej nie jest obsługiwany przez obudowę.",
        "ru": "Форм-фактор материнской платы не поддерживается корпусом.",
    },
    "gpu_too_long": {
        "uk": "Відеокарта довша за доступне місце на {difference_mm} мм і може впертися в кошик дисків або передній радіатор.",
        "en": "The GPU is {difference_mm} mm too long and may hit the drive cage or front radiator.",
        "pl": "Karta graficzna jest za długa o {difference_mm} mm i może kolidować z koszykiem dysków lub chłodnicą z przodu.",
        "ru": "Видеокарта длиннее доступного места на {difference_mm} мм и может упереться в корзину дисков или передний радиатор.",
    },
    "gpu_front_radiator_conflict": {
        "uk": "З переднім радіатором для відеокарти доступно {available_mm} мм, потрібно {required_mm} мм.",
        "en": "With the front radiator installed, the GPU has {available_mm} mm available but needs {required_mm} mm.",
        "pl": "Po montażu chłodnicy z przodu dla GPU zostaje {available_mm} mm, a potrzeba {required_mm} mm.",
        "ru": "С передним радиатором для видеокарты доступно {available_mm} мм, требуется {required_mm} мм.",
    },
    "gpu_too_tall": {
        "uk": "Відеокарта перевищує допустиму висоту на {difference_mm} мм.",
        "en": "The GPU exceeds the case height clearance by {difference_mm} mm.",
        "pl": "Karta graficzna przekracza dopuszczalną wysokość o {difference_mm} mm.",
        "ru": "Видеокарта превышает допустимую высоту на {difference_mm} мм.",
    },
    "gpu_too_thick": {
        "uk": "Відеокарта займає на {difference_slots} слота більше, ніж дозволяє корпус.",
        "en": "The GPU uses {difference_slots} more slots than the case allows.",
        "pl": "Karta zajmuje o {difference_slots} slotu więcej, niż pozwala obudowa.",
        "ru": "Видеокарта занимает на {difference_slots} слота больше, чем допускает корпус.",
    },
    "cooler_too_tall": {
        "uk": "Кулер вищий за ліміт корпусу на {difference_mm} мм.",
        "en": "The cooler exceeds the case height limit by {difference_mm} mm.",
        "pl": "Chłodzenie przekracza limit wysokości obudowy o {difference_mm} mm.",
        "ru": "Кулер выше лимита корпуса на {difference_mm} мм.",
    },
    "psu_form_factor_mismatch": {
        "uk": "Форм-фактор блока живлення не підтримується корпусом.",
        "en": "The PSU form factor is not supported by the case.",
        "pl": "Format zasilacza nie jest obsługiwany przez obudowę.",
        "ru": "Форм-фактор блока питания не поддерживается корпусом.",
    },
    "psu_too_long": {
        "uk": "Блок живлення довший за доступне місце на {difference_mm} мм.",
        "en": "The PSU exceeds the case length limit by {difference_mm} mm.",
        "pl": "Zasilacz przekracza limit długości obudowy o {difference_mm} mm.",
        "ru": "Блок питания длиннее доступного места на {difference_mm} мм.",
    },
    "psu_power_low": {
        "uk": "Потрібен блок живлення щонайменше приблизно на {required_w} Вт.",
        "en": "A power supply of roughly at least {required_w} W is required.",
        "pl": "Potrzebny jest zasilacz o mocy co najmniej około {required_w} W.",
        "ru": "Нужен блок питания минимум примерно на {required_w} Вт.",
    },
    "psu_connector_missing": {
        "uk": "У блока живлення немає потрібних роз'ємів GPU: {missing}.",
        "en": "The PSU is missing required GPU connectors: {missing}.",
        "pl": "Zasilacz nie ma wymaganych złączy GPU: {missing}.",
        "ru": "У блока питания нет необходимых разъёмов GPU: {missing}.",
    },
    "atx3_recommended": {
        "uk": "Для цієї відеокарти бажаний блок живлення ATX 3.x.",
        "en": "An ATX 3.x power supply is recommended for this GPU.",
        "pl": "Dla tej karty zalecany jest zasilacz ATX 3.x.",
        "ru": "Для этой видеокарты предпочтителен блок питания ATX 3.x.",
    },
    "psu_quality_headroom": {
        "uk": "Для потужної збірки краще блок живлення класу Gold або вище.",
        "en": "A Gold-rated or better PSU is recommended for a high-power build.",
        "pl": "Do mocnego zestawu zalecany jest zasilacz klasy Gold lub wyższej.",
        "ru": "Для мощной сборки лучше блок питания класса Gold или выше.",
    },
    "m2_slot_missing": {
        "uk": "На материнській платі немає слота M.2 для NVMe.",
        "en": "The motherboard has no M.2 slot for the NVMe drive.",
        "pl": "Płyta główna nie ma złącza M.2 dla dysku NVMe.",
        "ru": "На материнской плате нет слота M.2 для NVMe.",
    },
    "m2_size_unsupported": {
        "uk": "Форм-фактор накопичувача M.2 не підтримується платою.",
        "en": "The M.2 drive form factor is not supported by the board.",
        "pl": "Format dysku M.2 nie jest obsługiwany przez płytę.",
        "ru": "Форм-фактор накопителя M.2 не поддерживается платой.",
    },
    "storage_pcie_downshift": {
        "uk": "SSD працюватиме на швидкості старішої версії PCIe.",
        "en": "The SSD will run at the speed of an older PCIe generation.",
        "pl": "SSD będzie działać z prędkością starszej generacji PCIe.",
        "ru": "SSD будет работать на скорости более старой версии PCIe.",
    },
    "sata_port_missing": {
        "uk": "На платі немає доступного SATA-порту.",
        "en": "The motherboard has no available SATA port.",
        "pl": "Płyta główna nie ma dostępnego portu SATA.",
        "ru": "На плате нет доступного SATA-порта.",
    },
    "front_usb_c_unavailable": {
        "uk": "Передній USB-C корпусу не можна підключити до цієї плати.",
        "en": "The case front USB-C port cannot be connected to this motherboard.",
        "pl": "Przedniego USB-C obudowy nie da się podłączyć do tej płyty.",
        "ru": "Передний USB-C корпуса нельзя подключить к этой плате.",
    },
    "fan_headers_low": {
        "uk": "Для всіх вентиляторів потрібен розгалужувач або хаб.",
        "en": "A splitter or fan hub is required for all case fans.",
        "pl": "Do wszystkich wentylatorów potrzebny jest rozdzielacz lub hub.",
        "ru": "Для всех вентиляторов понадобится разветвитель или хаб.",
    },
}


def normalize_language(language: str | None) -> str:
    if not language:
        return "ru"
    value = language.lower().split("-")[0]
    return value if value in SUPPORTED_LANGUAGES else "ru"


def detect_language(text: str) -> str:
    lowered = text.lower()
    if re.search(r"[іїєґ]", lowered) or any(
        token in lowered for token in ("потрібен", "збірка", "відеокарта", "майбутнього")
    ):
        return "uk"
    if re.search(r"[ąćęłńóśźż]", lowered) or any(
        token in lowered for token in ("potrzebuję", "komputer", "budżet", "cichy", "zestaw")
    ):
        return "pl"
    if re.search(r"[а-яё]", lowered):
        return "ru"
    return "en"


def language_name(language: str | None) -> str:
    return LANGUAGE_NAMES[normalize_language(language)]


def profile_title(profile: str, language: str | None = None) -> str:
    lang = normalize_language(language)
    return PROFILE_TITLES.get(profile, {}).get(lang, profile.replace("_", " ").title())


def text(key: str, language: str | None = None, **params: Any) -> str:
    lang = normalize_language(language)
    template = TEXTS.get(key, {}).get(lang) or TEXTS.get(key, {}).get("en") or key
    return _safe_format(template, params)


def compatibility_message(
    code: str,
    language: str | None,
    details: dict[str, Any] | None = None,
    fallback: str = "",
) -> str:
    lang = normalize_language(language)
    template = COMPATIBILITY_MESSAGES.get(code, {}).get(lang)
    if not template:
        return fallback or code.replace("_", " ")
    return _safe_format(template, details or {})


def _safe_format(template: str, params: dict[str, Any]) -> str:
    class SafeDict(dict):
        def __missing__(self, key: str) -> str:
            return "?"

    return template.format_map(SafeDict(params))
