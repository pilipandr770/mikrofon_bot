import asyncio
import os
import sys
import argparse
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mikrofon_bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MikrofonBot")

# Для Windows используем правильную политику eventloop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def run_check():
    """Выполняет однократную проверку RSS и обработку новых записей"""
    from modules.scheduler import check_rss, process_next_publication
    
    logger.info("Начинаем проверку RSS...")
    has_new_entries = await check_rss()
    
    if has_new_entries:
        logger.info("Найдены новые записи, обрабатываем первую из них...")
        await process_next_publication()
    else:
        logger.info("Новых записей не найдено")

async def run_scheduler():
    """Запускает планировщик в постоянном режиме"""
    from modules.scheduler import run_scheduler_loop
    
    logger.info("Запускаем планировщик...")
    await run_scheduler_loop()

async def publish_next():
    """Публикует следующую запись из очереди"""
    from modules.scheduler import process_next_publication
    
    logger.info("Публикуем следующую запись из очереди...")
    result = await process_next_publication()
    
    if result:
        logger.info("Публикация успешно выполнена")
    else:
        logger.info("Не удалось опубликовать запись или очередь пуста")

async def view_queue():
    """Показывает текущую очередь публикаций"""
    from modules.rss_reader import load_publication_queue
    
    queue = load_publication_queue()
    
    if not queue:
        print("Очередь публикаций пуста")
        return
    
    print(f"В очереди {len(queue)} публикаций:")
    for i, entry in enumerate(queue):
        print(f"{i+1}. [{entry['source']}] {entry['title']}")
        print(f"   ID: {entry['id']}")
        print(f"   Добавлено: {entry['timestamp']}")
        print()

if __name__ == "__main__":
    # Создаем директории для вывода, если их нет
    if not os.path.exists("output"):
        os.makedirs("output")
    
    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser(description="MikrofonBot - RSS агрегатор с публикацией в соцсети")
    parser.add_argument("--scheduler", action="store_true", help="Запустить в режиме планировщика")
    parser.add_argument("--check", action="store_true", help="Выполнить проверку RSS")
    parser.add_argument("--publish", action="store_true", help="Опубликовать следующую запись из очереди")
    parser.add_argument("--queue", action="store_true", help="Показать текущую очередь публикаций")
    
    args = parser.parse_args()
    
    # Выбираем режим работы
    if args.scheduler:
        asyncio.run(run_scheduler())
    elif args.check:
        asyncio.run(run_check())
    elif args.publish:
        asyncio.run(publish_next())
    elif args.queue:
        asyncio.run(view_queue())
    else:
        # По умолчанию выполняем однократную проверку
        print("Запускаем однократную проверку. Используйте --scheduler для постоянной работы.")
        asyncio.run(run_check())