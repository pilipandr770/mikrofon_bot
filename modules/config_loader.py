import os
import json

CONFIG_PATH = "config/config.json"

def load_config():
    config = {
        "serpapi_key": os.getenv("SERPAPI_KEY"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "assistant_id": os.getenv("ASSISTANT_ID"),
        "telegram_token": os.getenv("TELEGRAM_TOKEN"),
        "telegram_channel_id": os.getenv("TELEGRAM_CHANNEL_ID"),
    }
    # Если хотя бы один ключ не найден — читаем из файла
    if not all(config.values()):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    return config
