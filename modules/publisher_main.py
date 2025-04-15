import os
import json
import time
from datetime import datetime
from modules.config_loader import load_config
from modules.publisher import telegram  # інші платформи згодом

PLAN_DIR = "output"
SUPPORTED_LANGS = ["uk", "en", "de"]

# 🛠 Автоматично створюємо output/, якщо його немає
os.makedirs(PLAN_DIR, exist_ok=True)

def get_today_plan():
    today_str = datetime.today().strftime("%Y-%m-%d")
    for folder in os.listdir(PLAN_DIR):
        subdir = os.path.join(PLAN_DIR, folder)
        if os.path.isdir(subdir):
            plan_path = os.path.join(subdir, f"plan_{today_str}.json")
            if os.path.exists(plan_path):
                with open(plan_path, "r", encoding="utf-8") as f:
                    plan = json.load(f)
                return plan, plan_path
    return None, None

def publish_all_languages():
    plan, path = get_today_plan()
    if not plan:
        print("❌ План не знайдено на сьогодні")
        return

    for lang in SUPPORTED_LANGS:
        print(f"🌍 Публікуємо мовою: {lang.upper()}")
        for i, post in enumerate(plan["posts"]):
            if post.get("status") != "translated":
                continue

            if post.get(f"status_{lang}") == "published":
                continue

            text = post.get("translations", {}).get(lang)
            image_name = f"image_{str(i+1).zfill(3)}.png"
            image_path = os.path.join(PLAN_DIR, plan["source"], image_name)

            if not text or not os.path.exists(image_path):
                print(f"⚠️ Пропущено пост {i+1} ({lang}) — немає тексту або картинки")
                continue

            success = telegram.send_telegram(text, image_path, lang)
            if success:
                post[f"status_{lang}"] = "published"
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(plan, f, ensure_ascii=False, indent=2)
                print(f"✅ Опубліковано пост {i+1} ({lang})")
                time.sleep(2)
            else:
                print(f"❌ Не вдалося опублікувати пост {i+1} ({lang})")

def publish_next_set():
    plan, path = get_today_plan()
    if not plan:
        print("❌ План не знайдено на сьогодні")
        return

    for i, post in enumerate(plan["posts"]):
        if post.get("status") != "translated":
            continue
        if all(post.get(f"status_{lang}") == "published" for lang in SUPPORTED_LANGS):
            continue

        for lang in SUPPORTED_LANGS:
            if post.get(f"status_{lang}") == "published":
                continue
            text = post.get("translations", {}).get(lang)
            image_name = f"image_{str(i+1).zfill(3)}.png"
            image_path = os.path.join(PLAN_DIR, plan["source"], image_name)
            if not text or not os.path.exists(image_path):
                print(f"⚠️ Пропущено пост {i+1} ({lang}) — немає тексту або картинки")
                continue
            success = telegram.send_telegram(text, image_path, lang)
            if success:
                post[f"status_{lang}"] = "published"
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(plan, f, ensure_ascii=False, indent=2)
                print(f"✅ Опубліковано пост {i+1} ({lang})")
            else:
                print(f"❌ Не вдалося опублікувати пост {i+1} ({lang})")
        break
    else:
        print("✅ Всі пости на сьогодні вже опубліковані!")

if __name__ == "__main__":
    import schedule
    print("⏳ Publisher запущено. Публікація кожні 2 години...")
    schedule.every(2).hours.do(publish_next_set)
    publish_next_set()
    while True:
        schedule.run_pending()
        time.sleep(60)
