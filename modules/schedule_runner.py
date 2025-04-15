import schedule
import time
import subprocess
from datetime import datetime

# Параметри часу
MAIN_TIME = "09:00"
PUBLISH_INTERVAL_HOURS = 2  # Публікація кожні 2 години
CLEAN_DAY = "sunday"
CLEAN_TIME = "06:00"

# Шлях до файлів
MAIN_SCRIPT = "main.py"
PUBLISH_SCRIPT = "publisher.py"
CLEAN_SCRIPT = "cleaner.py"

def run_script(script):
    print(f"▶️ Запуск: {script} | {datetime.now().strftime('%H:%M:%S')}")
    subprocess.run(["python", script])

# Щоденне оновлення контенту
schedule.every().day.at(MAIN_TIME).do(run_script, MAIN_SCRIPT)

# Публікація кожні N годин
for hour in range(10, 22, PUBLISH_INTERVAL_HOURS):
    schedule.every().day.at(f"{hour:02}:00").do(run_script, PUBLISH_SCRIPT)

# Очищення раз на тиждень
getattr(schedule.every(), CLEAN_DAY).at(CLEAN_TIME).do(run_script, CLEAN_SCRIPT)

print("✅ Schedule запущено. Очікуємо подій...")

while True:
    schedule.run_pending()
    time.sleep(60)
