"""Проверка токена и получение ID группы kolesadeshevo."""
import json
import urllib.parse
import urllib.request

from config import VK_GROUP_ID, VK_TOKEN


def main() -> None:
    if not VK_TOKEN:
        print("Ошибка: VK_TOKEN не задан в .env")
        return

    params = urllib.parse.urlencode(
        {
            "access_token": VK_TOKEN,
            "screen_name": "kolesadeshevo",
            "v": "5.199",
        }
    )
    url = f"https://api.vk.com/method/groups.getById?{params}"

    with urllib.request.urlopen(url) as response:
        data = json.load(response)

    if "error" in data:
        print("Ошибка VK API:", data["error"].get("error_msg"))
        return

    group = data["response"]["groups"][0]
    group_id = group["id"]
    name = group["name"]

    print(f"Сообщество: {name}")
    print(f"VK_GROUP_ID={group_id}")
    print()
    if VK_GROUP_ID != group_id:
        print("Добавьте в .env строку:")
        print(f"VK_GROUP_ID={group_id}")
    else:
        print("VK_GROUP_ID в .env уже совпадает.")


if __name__ == "__main__":
    main()
