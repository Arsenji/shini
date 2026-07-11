import logging
import random
import time

import vk_api
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.exceptions import ApiError

from config import VK_GROUP_ID, VK_TOKEN
from database import init_db
from handlers import WELCOME_TEXT, handle_message
from keyboards import main_keyboard, size_hint_keyboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_keyboard(keyboard_type: str | None) -> str | None:
    if keyboard_type == "main":
        return main_keyboard()
    if keyboard_type == "size_hint":
        return size_hint_keyboard()
    return main_keyboard()


def send_message(vk, user_id: int, text: str, keyboard: str | None = None) -> None:
    params = {
        "user_id": user_id,
        "message": text,
        "random_id": random.randint(1, 2_000_000_000),
    }
    if keyboard:
        params["keyboard"] = keyboard

    try:
        vk.messages.send(**params)
    except ApiError as error:
        # 912 — не включён режим «Чат-бот» или клавиатура недоступна
        if error.code == 912 and keyboard:
            logger.warning("Клавиатура недоступна (912), отправляем текст без кнопок")
            params.pop("keyboard", None)
            vk.messages.send(**params)
            return
        raise


def run_bot() -> None:
    if not VK_TOKEN or VK_GROUP_ID <= 0:
        raise RuntimeError(
            "Укажите VK_TOKEN и VK_GROUP_ID в файле .env\n"
            "Пример: см. .env.example"
        )

    init_db()

    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, VK_GROUP_ID)

    logger.info("Бот запущен. GROUP_ID=%s", VK_GROUP_ID)

    for event in longpoll.listen():
        if event.type != VkBotEventType.MESSAGE_NEW:
            continue

        message = event.object.message
        user_id = message["from_id"]
        text = message.get("text", "")

        logger.info("Сообщение от %s: %s", user_id, text)

        try:
            if message.get("action", {}).get("type") == "chat_invite_user":
                reply, keyboard_type = WELCOME_TEXT, "main"
            else:
                reply, keyboard_type = handle_message(text)

            send_message(vk, user_id, reply, get_keyboard(keyboard_type))
        except ApiError as error:
            logger.error("VK API ошибка [%s]: %s", error.code, error)
            if error.code == 912:
                logger.error(
                    "Включите «Чат-бот» в VK: Управление → Сообщения → Настройки для бота"
                )
            try:
                send_message(
                    vk,
                    user_id,
                    "Не удалось отправить ответ. Позвоните: +7 912 765 30 18",
                )
            except ApiError:
                logger.exception("Повторная отправка тоже не удалась")
        except Exception:
            logger.exception("Ошибка обработки сообщения")
            try:
                send_message(
                    vk,
                    user_id,
                    "Произошла ошибка. Попробуйте позже или позвоните: +7 912 765 30 18",
                )
            except ApiError:
                logger.exception("Не удалось отправить сообщение об ошибке")

        time.sleep(0.35)


if __name__ == "__main__":
    run_bot()
