import os
import json
import time
from openai import OpenAI
from modules.config_loader import load_config

PLAN_DIR = "output"

client = OpenAI(api_key=load_config()["openai_api_key"])


def load_today_plan():
    today = time.strftime("%Y-%m-%d")
    path = os.path.join(PLAN_DIR, f"plan_{today}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"План на {today} не знайдено: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), path


def save_plan(plan, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)


def translate_text(text, target_language):
    prompt = f"""
    Translate the following text into {target_language}. Keep it professional and suitable for social media:

    {text}
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()


def translate_filled_posts():
    plan, path = load_today_plan()
    post_count = 0

    for i, post in enumerate(plan["posts"]):
        if post.get("status") != "filled":
            continue

        print(f"🌐 Перекладаємо пост {i+1}: {post['title']}")
        try:
            uk_text = post["text"]
            en_text = translate_text(uk_text, "English")
            de_text = translate_text(uk_text, "German")

            post["translations"] = {
                "uk": uk_text,
                "en": en_text,
                "de": de_text
            }
            post["status"] = "translated"
            print("✅ Переклад завершено")
            post_count += 1

        except Exception as e:
            print(f"❌ Помилка при перекладі: {e}")
            post["status"] = "error"

        save_plan(plan, path)

    print(f"🔄 Переклад завершено. Успішно: {post_count} постів")


def translate_filled_plan(plan=None):
    """
    Переводит все заполненные посты в плане. Если план не передан — работает как translate_filled_posts (через файл).
    """
    if plan is None:
        translate_filled_posts()
        return
    post_count = 0
    for i, post in enumerate(plan["posts"]):
        if post.get("status") != "filled":
            continue
        uk_text = post["text"]
        en_text = translate_text(uk_text, "English")
        de_text = translate_text(uk_text, "German")
        post["translations"] = {
            "uk": uk_text,
            "en": en_text,
            "de": de_text
        }
        post["status"] = "translated"
        post_count += 1
    return plan


if __name__ == "__main__":
    translate_filled_posts()
