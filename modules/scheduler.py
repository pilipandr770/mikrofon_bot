import os
import json
import logging
from datetime import datetime
from modules.rss_reader import get_all_rss_entries
from modules.planner import create_daily_plan
from modules.post_filler import fill_plan_with_content
from modules.translator import translate_filled_plan

logger = logging.getLogger("Scheduler")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

OUTPUT_DIR = "output"

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def get_today_plan_path(source):
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    return os.path.join(OUTPUT_DIR, source, f"plan_{today_str}.json")

def load_or_create_plan(source, entries):
    plan_path = get_today_plan_path(source)
    if os.path.exists(plan_path):
        logger.info(f"📄 План уже існує: {plan_path}")
        with open(plan_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        logger.info(f"🧠 Генеруємо новий план для: {source}")
        plan = create_daily_plan(entries)
        ensure_dir(os.path.dirname(plan_path))
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        return plan

def is_publication_due():
    """
    Проверяет, пора ли публиковать следующий пост.
    Сейчас всегда возвращает True (заглушка).
    """
    return True

async def process_next_publication():
    """
    Асинхронно публикует следующий пост из очереди публикаций.
    Здесь должна быть логика публикации (например, через publisher), сейчас просто заглушка.
    """
    from modules.rss_reader import get_next_publication, remove_from_queue
    entry = get_next_publication()
    if entry:
        print(f"Публикуем: {entry['title']} ({entry['link']})")
        # Здесь можно вызвать: await publisher.publish_post(entry)
        remove_from_queue(entry["id"])
    else:
        print("Очередь публикаций пуста.")

def main():
    logger.info("🔁 Починаємо цикл створення та обробки плану публікацій")
    all_entries = get_all_rss_entries()

    for source, entries in all_entries.items():
        plan = load_or_create_plan(source, entries)

        # Перевіряємо, чи є пости без контенту
        if any("text" not in post for post in plan["posts"]):
            logger.info(f"✍️ Заповнюємо план контентом: {source}")
            plan = fill_plan_with_content(plan)

        # Перевіряємо, чи є переклади
        if any("translations" not in post for post in plan["posts"]):
            logger.info(f"🌐 Перекладаємо пости: {source}")
            plan = translate_filled_plan(plan)

        # Зберігаємо оновлений план
        plan_path = get_today_plan_path(source)
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ План збережено: {plan_path}")

if __name__ == "__main__":
    main()