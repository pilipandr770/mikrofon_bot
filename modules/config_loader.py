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
    # Если все ключи есть в окружении — используем их
    if all(config.values()):
        return config
    # Если хотя бы одного ключа не хватает — пробуем загрузить из файла
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    # Если нет ни файла, ни переменных — выбрасываем ошибку
    raise FileNotFoundError("config/config.json не найден и переменные окружения не заданы")