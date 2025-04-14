import asyncio
import os
import time
import json
import datetime
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("Scheduler")

# Константы
SCHEDULE_CONFIG_FILE = "schedule_config.json"
LAST_CHECK_FILE = "last_check.json"
DEFAULT_CHECK_HOUR = 7  # Проверка RSS в 7 утра
PUBLICATION_INTERVAL_HOURS = 3  # Публикация каждые 3 часа

def load_last_check():
    """Загружает время последней проверки новостей"""
    if os.path.exists(LAST_CHECK_FILE):
        with open(LAST_CHECK_FILE, 'r') as f:
            return json.load(f)
    return {
        "rss_check": None,
        "last_publication": None
    }

def save_last_check(check_type, timestamp=None):
    """Сохраняет время последней проверки или публикации"""
    data = load_last_check()
    data[check_type] = timestamp or datetime.datetime.now().isoformat()
    with open(LAST_CHECK_FILE, 'w') as f:
        json.dump(data, f)

def should_check_rss():
    """Проверяет, нужно ли проверять RSS-ленту сегодня"""
    last_data = load_last_check()
    last_check = last_data.get("rss_check")
    
    if not last_check:
        return True
    
    # Преобразуем строку в объект datetime
    last_check_dt = datetime.datetime.fromisoformat(last_check)
    now = datetime.datetime.now()
    
    # Проверяем, был ли уже сегодня запуск проверки RSS после заданного часа
    return (last_check_dt.date() < now.date()) and (now.hour >= DEFAULT_CHECK_HOUR)

async def check_rss():
    """Проверяет RSS-ленту и добавляет новые статьи в очередь"""
    from modules.rss_reader import fetch_latest_entries
    
    logger.info("Checking RSS feeds...")
    new_entries = fetch_latest_entries()
    
    if new_entries:
        logger.info(f"Found {len(new_entries)} new entries")
        for entry in new_entries:
            logger.info(f"Added to queue: {entry['title']} from {entry['source']}")
    else:
        logger.info("No new entries found")
    
    # Обновляем время последней проверки
    save_last_check("rss_check")
    
    return bool(new_entries)

def is_publication_due():
    """Проверяет, прошло ли достаточно времени с момента последней публикации"""
    last_data = load_last_check()
    last_publication = last_data.get("last_publication")
    
    if not last_publication:
        return True
    
    # Преобразуем строку в объект datetime
    last_pub_dt = datetime.datetime.fromisoformat(last_publication)
    now = datetime.datetime.now()
    
    # Проверяем, прошло ли нужное количество часов с момента последней публикации
    time_diff = now - last_pub_dt
    hours_passed = time_diff.total_seconds() / 3600
    
    return hours_passed >= PUBLICATION_INTERVAL_HOURS

async def process_next_publication():
    """Обрабатывает следующую публикацию из очереди"""
    from modules.rss_reader import get_next_publication, remove_from_queue
    from modules.article_writer import generate_article
    from modules.translator import translate_article_multilang
    from modules.image_generator import generate_and_save_image
    from modules.publisher.telegram import send_telegram
    
    entry = get_next_publication()
    
    if not entry:
        logger.info("No publications in queue")
        return False
    
    logger.info(f"Processing next publication: {entry['title']} from {entry['source']}")
    
    try:
        # Генерируем статью
        logger.info("Generating article...")
        article_file, article_content = await generate_article(entry)
        
        # Выделяем идентификатор файла
        source_name = entry["source"]
        file_id = entry["id"].split("/")[-2] if "/" in entry["id"] else entry["id"]
        
        # Переводим статью
        logger.info("Translating article...")
        translations = translate_article_multilang(article_content, source_name, file_id)
        
        # Генерируем изображение
        logger.info("Generating image...")
        image_path = generate_and_save_image(article_content, source_name, file_id)
        
        # Публикуем в Telegram на немецком языке
        logger.info("Publishing to Telegram (DE)...")
        de_text = translations["de"]
        send_telegram(de_text, image_path)
        
        # Удаляем из очереди
        logger.info(f"Publication successful, removing from queue: {entry['id']}")
        remove_from_queue(entry["id"])
        
        # Обновляем время последней публикации
        save_last_check("last_publication")
        
        logger.info("Publication process completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error processing publication: {e}", exc_info=True)
        return False

async def run_scheduler_once():
    """Выполняет однократную проверку расписания и обработку задач"""
    # Проверяем, нужно ли проверить RSS сегодня
    if should_check_rss():
        await check_rss()
    
    # Проверяем, нужно ли публиковать следующую статью
    if is_publication_due():
        await process_next_publication()

async def run_scheduler_loop():
    """Запускает бесконечный цикл планировщика"""
    logger.info("Starting scheduler loop")
    
    while True:
        try:
            await run_scheduler_once()
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}", exc_info=True)
        
        # Проверяем расписание каждые 15 минут
        await asyncio.sleep(15 * 60)

if __name__ == "__main__":
    # Для тестирования планировщика напрямую
    asyncio.run(run_scheduler_once())