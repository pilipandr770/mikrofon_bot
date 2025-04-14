#!/usr/bin/env python
"""
Этот скрипт предназначен для запуска по расписанию через cron или планировщик задач Windows.
Он выполняет соответствующие действия в зависимости от времени запуска:
- Утром: проверяет RSS и добавляет новые записи в очередь
- В течение дня: публикует статьи через определенные интервалы
"""

import sys
import os
import asyncio
import datetime
import logging
import argparse

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "schedule_runner.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ScheduleRunner")

# Для Windows используем правильную политику eventloop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def daily_check():
    """Утренняя проверка RSS"""
    from modules.scheduler import check_rss
    
    logger.info("Выполняем ежедневную проверку RSS...")
    await check_rss()
    logger.info("Проверка завершена")

async def publish_next():
    """Публикация следующей записи из очереди"""
    from modules.scheduler import process_next_publication, is_publication_due
    
    if is_publication_due():
        logger.info("Время для публикации следующей статьи...")
        await process_next_publication()
    else:
        logger.info("Еще не время для публикации следующей статьи")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MikrofonBot Schedule Runner")
    parser.add_argument("--mode", choices=["check", "publish"], 
                        help="Режим работы: check для утренней проверки, publish для публикации")
    
    args = parser.parse_args()
    
    # Определяем действие по времени, если режим не указан явно
    if not args.mode:
        now = datetime.datetime.now()
        # Утренняя проверка (между 7 и 8 утра)
        if 7 <= now.hour < 8:
            args.mode = "check"
        else:
            args.mode = "publish"
    
    # Запускаем соответствующую функцию
    if args.mode == "check":
        asyncio.run(daily_check())
    else:  # publish
        asyncio.run(publish_next())