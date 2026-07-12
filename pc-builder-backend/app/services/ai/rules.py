import re
from typing import Any

from app.schemas.builds import BuildRequirements, CompatibilityIssue
from app.services.ai.base import AIProvider


class RuleBasedAIProvider(AIProvider):
    name = "rules"
    model = "rules-v2"

    async def parse_requirements(self, prompt: str) -> BuildRequirements:
        text = prompt.lower().replace(" ", " ")
        budget = self._budget(text)
        currency = (
            "EUR"
            if "eur" in text or "евро" in text
            else "USD"
            if "$" in text or "usd" in text
            else "PLN"
        )
        purposes: list[str] = []
        mapping = {
            "gaming": ["игр", "gaming", "fps", "киберспорт"],
            "video_editing": ["монтаж", "premiere", "davinci", "4k видео", "after effects"],
            "programming": ["программ", "код", "docker", "виртуал", "разработ"],
            "streaming": ["стрим", "obs"],
            "ai": ["нейросет", "машинн", "stable diffusion", "llm", "ai"],
            "office": ["офис", "браузер", "word", "учеб"],
        }
        for purpose, words in mapping.items():
            if any(word in text for word in words):
                purposes.append(purpose)
        if not purposes:
            purposes = ["universal"]

        resolution = None
        if re.search(r"\b(8k|7680)", text):
            resolution = "8k"
        elif re.search(r"\b(4k|2160p|3840)", text):
            resolution = "4k"
        elif re.search(r"\b(1440p|2k|qhd|2560)", text):
            resolution = "1440p"
        elif re.search(r"\b(1080p|full\s*hd|fhd|1920)", text):
            resolution = "1080p"

        fps_match = re.search(r"(\d{2,3})\s*(?:fps|фпс|кадр)", text)
        target_fps = int(fps_match.group(1)) if fps_match else None
        low_noise = any(word in text for word in ["тих", "бесшум", "low noise", "silent"])
        upgradeability = (
            "high" if any(word in text for word in ["апгрейд", "будущее", "запас"]) else "medium"
        )
        cpu_brand = (
            "AMD"
            if "ryzen" in text or "amd процесс" in text
            else "Intel"
            if "intel" in text or "core i" in text
            else None
        )
        gpu_brand = (
            "NVIDIA"
            if any(word in text for word in ["nvidia", "rtx", "geforce"])
            else "AMD"
            if any(word in text for word in ["radeon", "rx "])
            else "Intel"
            if "arc" in text
            else None
        )
        storage_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(tb|тб|gb|гб)", text)
        storage_gb = 1000
        if storage_match:
            amount = float(storage_match.group(1).replace(",", "."))
            storage_gb = int(amount * 1000 if storage_match.group(2) in {"tb", "тб"} else amount)
        ram_match = re.search(
            r"(16|24|32|48|64|96|128|192|256)\s*(?:gb|гб).*?(?:ram|озу|памят)", text
        )
        if not ram_match:
            ram_match = re.search(
                r"(?:ram|озу|памят).*?(16|24|32|48|64|96|128|192|256)\s*(?:gb|гб)", text
            )
        ram_gb = (
            int(ram_match.group(1))
            if ram_match
            else (64 if "video_editing" in purposes or "ai" in purposes else 32)
        )
        max_stores = None
        stores_match = re.search(r"(?:не больше|максимум|max)\s*(\d)\s*магаз", text)
        if stores_match:
            max_stores = int(stores_match.group(1))

        return BuildRequirements(
            budget=budget,
            currency=currency,
            purposes=purposes,
            resolution=resolution,
            target_fps=target_fps,
            low_noise=low_noise,
            upgradeability=upgradeability,
            rgb=True
            if "rgb" in text or "подсвет" in text
            else False
            if "без rgb" in text
            else None,
            case_color="white" if "бел" in text else "black" if "черн" in text else None,
            cpu_brand=cpu_brand,
            gpu_brand=gpu_brand,
            storage_gb=max(500, storage_gb),
            ram_gb=ram_gb,
            include_wifi="wifi" in text or "wi-fi" in text or "вайф" in text,
            include_bluetooth="bluetooth" in text or "блют" in text,
            overclocking="разгон" in text or "overclock" in text,
            max_store_count=max_stores,
        )

    @staticmethod
    def _budget(text: str) -> float:
        patterns = [
            r"(?:до|бюджет|budget)\s*(?:примерно|около|~)?\s*(\d[\d\s.,]*)",
            r"(\d[\d\s.,]*)\s*(?:pln|зл|zł|евро|eur|usd|\$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                raw = match.group(1).replace(" ", "").replace(",", ".")
                try:
                    value = float(raw)
                    if 1500 <= value <= 500000:
                        return value
                except ValueError:
                    continue
        return 6000

    async def explain_build(
        self,
        requirements: BuildRequirements,
        profile: str,
        components: list[dict[str, Any]],
        total_price: float,
    ) -> str:
        names = {item["category"]: item["name"] for item in components}
        profile_text = {
            "max_performance": "максимальный результат сейчас",
            "balanced": "ровный баланс скорости, качества и цены",
            "quiet": "низкий шум и хороший температурный запас",
            "upgrade_ready": "современную платформу и будущий апгрейд",
            "best_value": "максимум пользы за каждый злотый",
        }.get(profile, "сбалансированную работу")
        purposes = ", ".join(requirements.purposes)
        return (
            f"Вариант рассчитан на {profile_text}. Связка {names.get('cpu', 'CPU')} и "
            f"{names.get('gpu', 'GPU')} подходит под задачи: {purposes}. Плата, память, охлаждение, "
            f"корпус и питание прошли детерминированную проверку совместимости. Итог с выбранной "
            f"доставкой составляет {total_price:.2f} {requirements.currency}."
        )

    async def explain_compatibility(self, issues: list[CompatibilityIssue]) -> str:
        if not issues:
            return "Компоненты совместимы по проверяемым параметрам."
        return " ".join(f"{index + 1}) {issue.message}" for index, issue in enumerate(issues))
