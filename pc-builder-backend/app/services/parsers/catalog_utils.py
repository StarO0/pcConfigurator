from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any

CATEGORY_ALIASES = {
    "cpu": ("procesor", "processor", "cpu"),
    "motherboard": ("plyta glowna", "motherboard", "mainboard"),
    "gpu": ("karta graficzna", "graphics card", "gpu", "video card"),
    "ram": ("pamiec ram", "memory", "ram"),
    "storage": ("dysk ssd", "ssd", "hard drive", "storage", "dysk twardy"),
    "cooler": ("chlodzenie", "cpu cooler", "cooler"),
    "case": ("obudowa", "computer case", "case"),
    "psu": ("zasilacz", "power supply", "psu"),
    "monitor": ("monitor",),
    "keyboard": ("klawiatura", "keyboard"),
    "mouse": ("mysz", "mouse"),
    "headset": ("sluchawki", "headphones", "headset"),
    "ups": ("ups", "zasilacz awaryjny"),
    "fan": ("wentylator", "case fan", "computer fan"),
    "webcam": ("kamera internetowa", "webcam"),
    "speaker": ("głośnik", "glosnik", "speaker"),
    "microphone": ("mikrofon", "microphone"),
    "controller": ("kontroler gier", "gamepad", "controller"),
    "network": (
        "karta sieciowa",
        "karty sieciowe",
        "network card",
        "network adapter",
        "wi-fi adapter",
        "wifi adapter",
    ),
    "external-storage": ("dysk zewnętrzny", "dysk zewnetrzny", "external drive"),
    "optical-drive": ("napęd optyczny", "naped optyczny", "dvd writer", "blu-ray drive"),
    "sound-card": ("karta dźwiękowa", "karta dzwiekowa", "sound card"),
    "thermal-paste": ("pasta termoprzewodząca", "pasta termoprzewodzaca", "thermal paste"),
    "fan-controller": ("kontroler wentylatorów", "kontroler wentylatorow", "fan controller"),
    "case-accessory": ("akcesoria do obudów", "akcesoria do obudow", "case accessory"),
}


def fold(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def _category_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(
            _category_text(value.get(key)) for key in ("name", "title", "value", "@id", "url")
        )
    if isinstance(value, (list, tuple, set)):
        return " ".join(_category_text(item) for item in value)
    return str(value or "")


def normalize_category(value: Any, *, url: str = "", title: str = "") -> str:
    haystack = fold(" ".join((_category_text(value), url, title)))
    for category, aliases in CATEGORY_ALIASES.items():
        padded = f" {haystack} "
        if any(
            (f" {needle} " in padded if len(needle) <= 3 else needle in haystack)
            for alias in aliases
            if (needle := fold(alias))
        ):
            return category
    return "unknown"


def decimal_value(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float, Decimal)):
        text = str(value)
    else:
        text = re.sub(r"[^0-9,.-]", "", str(value).replace("\u00a0", ""))
        if "," in text and "." in text:
            text = (
                text.replace(".", "").replace(",", ".")
                if text.rfind(",") > text.rfind(".")
                else text.replace(",", "")
            )
        elif "," in text:
            text = text.replace(",", ".")
    try:
        result = Decimal(text).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None
    return result if result > 0 else None


def bool_stock(value: Any) -> bool:
    text = fold(str(value or ""))
    unavailable = ("outofstock", "soldout", "niedostep", "wycofan", "brak")
    return not any(token in text.replace(" ", "") for token in unavailable)
