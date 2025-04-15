import feedparser
import json
import os
from datetime import datetime

# Файл для збереження останньої обробленої новини
LAST_ID_FILE = "last_rss_id.json"
# Файл для очереди публикаций
PUBLICATION_QUEUE_FILE = "publication_queue.json"

# RSS-ленты
RSS_URLS = {
    "openai": "https://openai.com/blog/rss.xml",
    "google": "https://blog.google/rss/"
}

def load_last_ids():
    """Загружает последние ID для каждого источника"""
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, 'r') as f:
            data = json.load(f)
            # Для обратной совместимости с предыдущей версией
            if isinstance(data, dict) and "last_id" in data:
                return {"openai": data["last_id"], "google": ""}
            return data
    return {"openai": "", "google": ""}

def save_last_id(source, entry_id):
    """Сохраняет последний ID для указанного источника"""
    last_ids = load_last_ids()
    last_ids[source] = entry_id
    with open(LAST_ID_FILE, 'w') as f:
        json.dump(last_ids, f)

def load_publication_queue():
    """Загружает очередь публикаций"""
    if os.path.exists(PUBLICATION_QUEUE_FILE):
        with open(PUBLICATION_QUEUE_FILE, 'r') as f:
            return json.load(f)
    return []

def save_publication_queue(queue):
    """Сохраняет очередь публикаций"""
    with open(PUBLICATION_QUEUE_FILE, 'w') as f:
        json.dump(queue, f)

def add_to_publication_queue(entry):
    """Добавляет новую запись в очередь публикаций"""
    queue = load_publication_queue()
    queue.append(entry)
    save_publication_queue(queue)

def fetch_latest_entries():
    """Получает последние новости с обоих источников и добавляет их в очередь публикаций"""
    last_ids = load_last_ids()
    print(f"Last processed IDs: {last_ids}")
    
    new_entries = []
    
    # Проверяем все источники
    for source, url in RSS_URLS.items():
        print(f"Fetching RSS feed from: {url}")
        feed = feedparser.parse(url)
        
        if not feed.entries:
            print(f"WARNING: No entries found in the {source} RSS feed")
            continue
            
        print(f"Found {len(feed.entries)} entries in the {source} RSS feed")
        
        # Для отладки покажем первые 3 записи
        for i, entry in enumerate(feed.entries[:3]):
            print(f"Entry {i+1}: {entry.title} (ID: {entry.id})")
        
        # Берем первую запись для обработки
        entry = feed.entries[0]
        if entry.id != last_ids.get(source, ""):
            print(f"New entry found in {source}: {entry.title} with ID: {entry.id}")
            save_last_id(source, entry.id)
            
            new_entry = {
                "id": entry.id,
                "source": source,
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
                "summary": entry.summary if hasattr(entry, "summary") else entry.description,
                "timestamp": datetime.now().isoformat()
            }
            
            new_entries.append(new_entry)
            add_to_publication_queue(new_entry)
        else:
            print(f"Entry {entry.title} from {source} already processed (ID: {entry.id})")
    
    return new_entries

def fetch_all_news():
    """
    Получает свежие новости из всех источников (RSS), добавляет новые в очередь и возвращает сгруппированные по источникам.
    """
    fetch_latest_entries()
    return get_all_rss_entries()

def get_next_publication():
    """Получает следующую публикацию из очереди (но не удаляет ее)"""
    queue = load_publication_queue()
    if queue:
        return queue[0]
    return None

def remove_from_queue(entry_id):
    """Удаляет публикацию из очереди по ID"""
    queue = load_publication_queue()
    queue = [entry for entry in queue if entry["id"] != entry_id]
    save_publication_queue(queue)

def get_all_rss_entries():
    """
    Возвращает все записи из очереди публикаций, сгруппированные по источнику.
    Пример: {"google": [...], "openai": [...]} 
    """
    queue = load_publication_queue()
    grouped = {}
    for entry in queue:
        source = entry.get("source", "unknown")
        grouped.setdefault(source, []).append(entry)
    return grouped

if __name__ == "__main__":
    new_entries = fetch_latest_entries()
    if new_entries:
        print(f"Found {len(new_entries)} new entries:")
        for entry in new_entries:
            print(json.dumps(entry, indent=2))
    else:
        print("No new posts.")
