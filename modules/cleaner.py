import os
import shutil
from datetime import datetime, timedelta

OUTPUT_DIR = "output"
ARCHIVE_DIR = "archive"
KEEP_DAYS = 2  # Скільки днів зберігати (сьогодні + вчора)
ARCHIVE_MODE = True  # Якщо True — переносить у archive/, якщо False — видаляє


def get_date_suffixes_to_keep():
    today = datetime.today().date()
    return {(today - timedelta(days=i)).isoformat() for i in range(KEEP_DAYS)}


def clean_output():
    print("🧹 Очищення контенту... (режим архівації: {} )".format("УВІМКНЕНO" if ARCHIVE_MODE else "ВИМКНЕНO"))
    keep_suffixes = get_date_suffixes_to_keep()
    removed, archived = 0, 0

    for source in os.listdir(OUTPUT_DIR):
        source_dir = os.path.join(OUTPUT_DIR, source)
        if not os.path.isdir(source_dir):
            continue

        for filename in os.listdir(source_dir):
            file_path = os.path.join(source_dir, filename)

            # Якщо план на сьогодні/вчора — залишаємо
            if any(filename.endswith(f"plan_{suffix}.json") for suffix in keep_suffixes):
                continue

            try:
                if ARCHIVE_MODE:
                    archive_source_dir = os.path.join(ARCHIVE_DIR, source)
                    os.makedirs(archive_source_dir, exist_ok=True)
                    shutil.move(file_path, os.path.join(archive_source_dir, filename))
                    archived += 1
                    print(f"📦 Архівовано: {file_path}")
                else:
                    os.remove(file_path)
                    removed += 1
                    print(f"🗑 Видалено: {file_path}")
            except Exception as e:
                print(f"⚠️ Помилка при обробці {file_path}: {e}")

    print(f"✅ Завершено. Архівовано: {archived}, Видалено: {removed}")


if __name__ == "__main__":
    clean_output()
