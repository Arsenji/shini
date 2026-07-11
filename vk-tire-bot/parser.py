import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TireSize:
    width: int
    profile: int
    radius: int

    def label(self) -> str:
        return f"{self.width}/{self.profile} R{self.radius}"


# 205/55 R16, 205/55R16, 205-55-16, 205 55 16
SIZE_PATTERN = re.compile(
    r"(?P<width>\d{3})\s*[/\-]\s*(?P<profile>\d{2})\s*[/\-]?\s*(?:R|r)?\s*(?P<radius>\d{2})",
    re.IGNORECASE,
)

# Три числа подряд: 205 55 16
THREE_NUMBERS_PATTERN = re.compile(
    r"\b(?P<width>\d{3})\s+(?P<profile>\d{2})\s+(?P<radius>\d{2})\b"
)


def parse_tire_size(text: str) -> TireSize | None:
    """Извлекает размер шины из текста пользователя."""
    if not text:
        return None

    normalized = text.strip().replace(",", ".")

    match = SIZE_PATTERN.search(normalized)
    if not match:
        match = THREE_NUMBERS_PATTERN.search(normalized)

    if not match:
        return None

    width = int(match.group("width"))
    profile = int(match.group("profile"))
    radius = int(match.group("radius"))

    if not _is_valid_size(width, profile, radius):
        return None

    return TireSize(width=width, profile=profile, radius=radius)


def _is_valid_size(width: int, profile: int, radius: int) -> bool:
    return 125 <= width <= 355 and 25 <= profile <= 85 and 12 <= radius <= 24
