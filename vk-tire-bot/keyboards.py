from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from config import SITE_URL, VK_GROUP_URL


def main_keyboard() -> str:
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_line()
    keyboard.add_openlink_button("Наш сайт", link=SITE_URL)
    keyboard.add_openlink_button("Группа VK", link=VK_GROUP_URL)
    return keyboard.get_keyboard()


def size_hint_keyboard() -> str:
    keyboard = VkKeyboard(one_time=False, inline=False)
    keyboard.add_button("205/55 R16", color=VkKeyboardColor.SECONDARY)
    keyboard.add_button("215/60 R16", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("225/45 R17", color=VkKeyboardColor.SECONDARY)
    keyboard.add_button("195/65 R15", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()
