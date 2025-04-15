import time
import json
import os
from datetime import date

from modules import rss_reader, planner, post_filler, translator, image_generator, publisher_main as publisher

OUTPUT_DIR = "output"

def get_plan_path(source):
    today = date.today().isoformat()
    return os.path.join(OUTPUT_DIR, source, f"plan_{today}.json")

def save_plan(plan, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

def main():
    print("📥 1. Отримання новин із RSS та Reddit...")
    # Явно загружаем свежие новости и формируем очередь публикаций
    rss_reader.fetch_latest_entries()
    entries_by_source = rss_reader.get_all_rss_entries()

    for source, source_entries in entries_by_source.items():
        print(f"🗂 Джерело: {source} — {len(source_entries)} новин")
        plan_path = get_plan_path(source)
        # Если план уже есть — загружаем, иначе создаём новый
        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                plan = json.load(f)
            print("📄 План вже існує, завантажено")
        else:
            print("🧠 Генеруємо новий план...")
            plan_raw = planner.create_daily_plan(source_entries)
            # Проверка структуры результата
            if not isinstance(plan_raw, list) or not all(isinstance(post, dict) and "title" in post and "idea" in post for post in plan_raw):
                print("❌ Помилка: create_daily_plan повернув неочікувану структуру:", plan_raw)
                return
            plan = {
                "date": str(date.today()),
                "source": source,
                "posts": [
                    {"title": post["title"], "idea": post["idea"], "status": "empty"}
                    for post in plan_raw
                ]
            }
            os.makedirs(os.path.dirname(plan_path), exist_ok=True)
            save_plan(plan, plan_path)

        # Генерация текстов и промптов для всех пустых постов
        if any(post.get("status") == "empty" for post in plan["posts"]):
            print("✍️ 2. Генеруємо тексти та промпти...")
            plan = post_filler.fill_plan_with_content(plan)
            save_plan(plan, plan_path)

        # Перевод всех заполненных постов
        if any(post.get("status") == "filled" for post in plan["posts"]):
            print("🌐 3. Перекладаємо тексти...")
            plan = translator.translate_filled_plan(plan)
            save_plan(plan, plan_path)

        # Генерация изображений для всех постов, где есть промпт, но нет картинки
        if any("image_prompt" in post and not post.get("image_generated") for post in plan["posts"]):
            print("🖼 4. Генеруємо зображення...")
            plan = image_generator.generate_images_from_plan(plan)
            save_plan(plan, plan_path)

        # Публикация всех переведённых постов
        print("📤 5. Починаємо публікацію...")
        publisher.publish_all_languages()

if __name__ == "__main__":
    main()
    print("✅ Завершено!")
