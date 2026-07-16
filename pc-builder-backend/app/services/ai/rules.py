from __future__ import annotations

import re
from typing import Any

from app.schemas.builds import BuildRequirements, CompatibilityIssue
from app.services.ai.base import AIProvider
from app.services.i18n import detect_language, profile_title, text


class RuleBasedAIProvider(AIProvider):
    name = "rules"
    model = "rules-v3-multilingual"

    async def parse_requirements(self, prompt: str) -> BuildRequirements:
        text_value = prompt.lower().replace(" ", " ")
        language = detect_language(prompt)
        budget = self._budget(text_value)
        currency = self._currency(text_value)
        purposes: list[str] = []
        mapping = {
            "gaming": [
                "игр",
                "gaming",
                "game",
                "fps",
                "фпс",
                "кіберспорт",
                "gry",
                "grania",
                "esport",
            ],
            "video_editing": [
                "монтаж",
                "premiere",
                "davinci",
                "4k video",
                "4k відео",
                "after effects",
                "edycja wideo",
                "montaż",
                "video editing",
            ],
            "programming": [
                "программ",
                "програмув",
                "код",
                "coding",
                "programming",
                "programowanie",
                "docker",
                "виртуал",
                "wirtual",
                "разработ",
            ],
            "streaming": ["стрим", "стрім", "stream", "obs"],
            "ai": [
                "нейросет",
                "нейромереж",
                "машинн",
                "stable diffusion",
                "llm",
                "sztuczna inteligencja",
                "machine learning",
                " ai ",
            ],
            "office": [
                "офис",
                "офіс",
                "biuro",
                "office",
                "браузер",
                "browser",
                "word",
                "учеб",
                "навчан",
                "nauka",
            ],
        }
        for purpose, words in mapping.items():
            if any(word in text_value for word in words):
                purposes.append(purpose)
        if not purposes:
            purposes = ["universal"]

        resolution = None
        if re.search(r"\b(8k|7680)", text_value):
            resolution = "8k"
        elif re.search(r"\b(4k|2160p|3840)", text_value):
            resolution = "4k"
        elif re.search(r"\b(1440p|2k|qhd|2560)", text_value):
            resolution = "1440p"
        elif re.search(r"\b(1080p|full\s*hd|fhd|1920)", text_value):
            resolution = "1080p"

        fps_match = re.search(r"(\d{2,3})\s*(?:fps|фпс|кадр|klatek)", text_value)
        target_fps = int(fps_match.group(1)) if fps_match else None
        low_noise = any(
            word in text_value
            for word in [
                "тих",
                "тихий",
                "тиха",
                "бесшум",
                "безшум",
                "low noise",
                "silent",
                "cichy",
                "cicha",
            ]
        )
        upgradeability = (
            "high"
            if any(
                word in text_value
                for word in [
                    "апгрейд",
                    "майбут",
                    "будущее",
                    "запас",
                    "upgrade",
                    "rozbudow",
                    "przyszłość",
                ]
            )
            else "medium"
        )
        cpu_brand = (
            "AMD"
            if "ryzen" in text_value or "amd cpu" in text_value or "amd процесс" in text_value
            else "Intel"
            if "intel" in text_value or "core i" in text_value
            else None
        )
        gpu_brand = (
            "NVIDIA"
            if any(word in text_value for word in ["nvidia", "rtx", "geforce"])
            else "AMD"
            if any(word in text_value for word in ["radeon", "rx "])
            else "Intel"
            if "arc" in text_value
            else None
        )
        storage_gb = self._storage(text_value)
        ram_gb = self._ram(text_value, purposes)
        max_stores = None
        stores_match = re.search(
            r"(?:не больше|максимум|max|nie więcej niż)\s*(\d)\s*(?:магаз|sklep|store)",
            text_value,
        )
        if stores_match:
            max_stores = int(stores_match.group(1))

        workload_names = self._workloads(text_value)
        return BuildRequirements(
            budget=budget,
            currency=currency,
            purposes=purposes,
            resolution=resolution,
            target_fps=target_fps,
            low_noise=low_noise,
            upgradeability=upgradeability,
            rgb=True
            if "rgb" in text_value or "подсвет" in text_value or "підсвіт" in text_value
            else False
            if any(
                value in text_value for value in ["без rgb", "no rgb", "bez rgb", "без підсвітки"]
            )
            else None,
            case_color=self._case_color(text_value),
            cpu_brand=cpu_brand,
            gpu_brand=gpu_brand,
            storage_gb=max(500, storage_gb),
            ram_gb=ram_gb,
            include_wifi=any(value in text_value for value in ["wifi", "wi-fi", "вайф"]),
            include_bluetooth=any(
                value in text_value for value in ["bluetooth", "блют", "bluetooth"]
            ),
            overclocking=any(
                value in text_value for value in ["разгон", "розгін", "overclock", "podkręc"]
            ),
            max_store_count=max_stores,
            workload_names=workload_names,
            language=language,
        )

    @staticmethod
    def _currency(text_value: str) -> str:
        if any(value in text_value for value in ["eur", "евро", "євро", "euro", "€"]):
            return "EUR"
        if "$" in text_value or "usd" in text_value or "dollar" in text_value:
            return "USD"
        if any(value in text_value for value in ["uah", "грн", "₴"]):
            return "UAH"
        return "PLN"

    @staticmethod
    def _budget(text_value: str) -> float:
        patterns = [
            r"(?:до|бюджет|budget|budżet|бюджетом)\s*(?:примерно|около|~|około)?\s*(\d[\d\s.,]*)",
            r"(\d[\d\s.,]*)\s*(?:pln|зл|zł|евро|євро|eur|usd|uah|грн|\$|€|₴)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text_value)
            if match:
                raw = match.group(1).replace(" ", "").replace(",", ".")
                try:
                    value = float(raw)
                    if 1500 <= value <= 500000:
                        return value
                except ValueError:
                    continue
        return 6000

    @staticmethod
    def _storage(text_value: str) -> int:
        storage_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(tb|тб|gb|гб)", text_value)
        if not storage_match:
            return 1000
        amount = float(storage_match.group(1).replace(",", "."))
        return int(amount * 1000 if storage_match.group(2) in {"tb", "тб"} else amount)

    @staticmethod
    def _ram(text_value: str, purposes: list[str]) -> int:
        patterns = [
            r"(16|24|32|48|64|96|128|192|256)\s*(?:gb|гб).*?(?:ram|озу|памят)",
            r"(?:ram|озу|памят).*?(16|24|32|48|64|96|128|192|256)\s*(?:gb|гб)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text_value)
            if match:
                return int(match.group(1))
        return 64 if "video_editing" in purposes or "ai" in purposes else 32

    @staticmethod
    def _case_color(text_value: str) -> str | None:
        if any(value in text_value for value in ["бел", "білий", "white", "biały", "biała"]):
            return "white"
        if any(value in text_value for value in ["черн", "чорн", "black", "czarn"]):
            return "black"
        return None

    @staticmethod
    def _workloads(text_value: str) -> list[str]:
        matches = {
            "cyberpunk_2077": ["cyberpunk", "киберпанк", "кіберпанк"],
            "counter_strike_2": ["counter-strike", "counter strike", "cs2", "кс2"],
            "fortnite": ["fortnite", "фортнайт"],
            "premiere_pro_4k_export": ["premiere", "премьер", "прем'єр"],
            "davinci_resolve_4k_export": ["davinci", "да винчи", "давінчі"],
            "stable_diffusion_xl": ["stable diffusion", "sdxl"],
            "code_compile": ["compile", "компиля", "компіля", "kompilac"],
        }
        output = [
            slug for slug, words in matches.items() if any(word in text_value for word in words)
        ]
        return output

    async def explain_build(
        self,
        requirements: BuildRequirements,
        profile: str,
        components: list[dict[str, Any]],
        total_price: float,
    ) -> str:
        names = {item["category"]: item["name"] for item in components}
        return text(
            "build_explanation",
            requirements.language,
            profile=profile_title(profile, requirements.language),
            purposes=", ".join(requirements.purposes),
            cpu=names.get("cpu", "CPU"),
            gpu=names.get("gpu", "GPU"),
            price=total_price,
            currency=requirements.currency,
        )

    async def explain_compatibility(self, issues: list[CompatibilityIssue]) -> str:
        if not issues:
            return "OK"
        return " ".join(f"{index + 1}) {issue.message}" for index, issue in enumerate(issues))
