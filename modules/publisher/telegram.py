import os
import requests
import time
import json
from modules.config_loader import load_config

PLAN_DIR = "output"

def send_telegram(text, image_path, lang):
    config = load_config()
    token = config.get("telegram_token")
    # Получаем chat_id из config["telegram_channels"]
    chat_id = config.get("telegram_channels", {}).get(lang)

    if not token or not chat_id:
        print("Telegram token або channel ID не задані.")
        return False

    caption = text[:1024] if len(text) > 1024 else text

    with open(image_path, "rb") as img:
        files = {"photo": img}
        data = {
            "chat_id": chat_id,
            "caption": caption,
            "parse_mode": "HTML"
        }
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        response = requests.post(url, data=data, files=files)

    if response.status_code == 200:
        print(f"✅ Telegram ({lang}): Sent successfully")
        if len(text) > 1024:
            remainder = text[1024:]
            chunk_size = 4096
            for i in range(0, len(remainder), chunk_size):
                chunk = remainder[i:i + chunk_size]
                data = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML"
                }
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                r = requests.post(url, data=data)
                if r.status_code != 200:
                    print(f"❌ Telegram: Failed to send chunk ({lang})")
        return True
    else:
        print(f"❌ Telegram ({lang}): Failed. Status: {response.status_code}")
        return False


def publish_from_plan(language: str):
    today = time.strftime("%Y-%m-%d")
    plan_path = os.path.join(PLAN_DIR, f"plan_{today}.json")

    if not os.path.exists(plan_path):
        print(f"План не знайдено: {plan_path}")
        return

    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    for i, post in enumerate(plan["posts"]):
        if post.get("status") != "translated":
            continue

        lang_text = post.get("translations", {}).get(language)
        if not lang_text:
            print(f"⚠️ Немає перекладу для мови {language} у пості {i+1}")
            continue

        image_name = f"image_{str(i+1).zfill(3)}.png"
        image_path = os.path.join(PLAN_DIR, plan["source"], image_name)

        if not os.path.exists(image_path):
            print(f"⚠️ Зображення не знайдено: {image_path}")
            continue

        success = send_telegram(lang_text, image_path, language)
        if success:
            post[f"status_{language}"] = "published"
            with open(plan_path, "w", encoding="utf-8") as f:
                json.dump(plan, f, ensure_ascii=False, indent=2)
            print(f"📤 Опубліковано пост {i+1} ({language})")
            break  # Публікуємо лише один пост за раз
        else:
            print(f"❌ Помилка при публікації поста {i+1} ({language})")


if __name__ == "__main__":
    publish_from_plan("de")
