from parser import TireSize, parse_tire_size
from database import find_tires_by_size
from config import MAX_RESULTS, VK_GROUP_URL


WELCOME_TEXT = (
    "Здравствуйте! Я бот магазина КОЛЁСА ДЁШЕВО.\n\n"
    "Отправьте размер шины, и я подберу цены из наличия.\n"
    "Примеры: 205/55 R16 или 205 55 16"
)

HELP_TEXT = (
    "Как пользоваться ботом:\n\n"
    "1. Напишите размер шины в формате 205/55 R16\n"
    "2. Бот покажет модели и цены за 1 шину\n"
    "3. Для заказа позвоните: +7 912 765 30 18\n\n"
    f"Группа: {VK_GROUP_URL}"
)


def handle_message(text: str) -> tuple[str, str | None]:
    """
    Обрабатывает текст сообщения.
    Возвращает (ответ, тип_клавиатуры): main | size_hint | None
    """
    cleaned = text.strip()

    if not cleaned:
        return "Отправьте размер шины, например: 205/55 R16", "size_hint"

    lower = cleaned.lower()

    if lower in {"начать", "start", "меню", "привет", "здравствуйте"}:
        return WELCOME_TEXT, "main"

    if lower in {"помощь", "help", "?"}:
        return HELP_TEXT, "main"

    if lower in {"подобрать шины", "подбор", "цена", "стоимость"}:
        return (
            "Укажите размер шины.\n"
            "Например: 205/55 R16 или нажмите кнопку с размером ниже.",
            "size_hint",
        )

    size = parse_tire_size(cleaned)
    if size is None:
        return (
            "Не удалось распознать размер.\n\n"
            "Отправьте в формате:\n"
            "• 205/55 R16\n"
            "• 205-55-16\n"
            "• 205 55 16",
            "size_hint",
        )

    return format_price_response(size), "main"


def format_price_response(size: TireSize) -> str:
    offers = find_tires_by_size(size.width, size.profile, size.radius, limit=MAX_RESULTS)

    if not offers:
        return (
            f"По размеру {size.label()} сейчас нет позиций в базе.\n\n"
            "Позвоните нам для уточнения: +7 912 765 30 18"
        )

    lines = [f"Шины {size.label()} — цена за 1 шину:\n"]
    for i, offer in enumerate(offers, start=1):
        lines.append(
            f"{i}. {offer.brand} {offer.model}\n"
            f"   {offer.season_label} · {offer.price:,} ₽".replace(",", " ")
        )

    min_price = offers[0].price
    lines.append(f"\nОт {min_price:,} ₽ за шину".replace(",", " "))
    lines.append("\nДля заказа: +7 912 765 30 18")

    if len(offers) >= MAX_RESULTS:
        lines.append(f"\nПоказаны первые {MAX_RESULTS} позиций.")

    return "\n".join(lines)
