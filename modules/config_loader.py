import os
import json

CONFIG_PATH = "config/config.json"

def load_config():
    config = {}

    # Основні ключі з ENV
    config["openai_api_key"] = os.getenv("OPENAI_API_KEY")
    config["serpapi_key"] = os.getenv("SERPAPI_KEY")
    config["telegram_token"] = os.getenv("TELEGRAM_TOKEN")

    # Асистенти
    assistants_env = {
        "planner": os.getenv("PLANNER_ID"),
        "writer": os.getenv("WRITER_ID"),
        "translator": os.getenv("TRANSLATOR_ID")
    }
    config["assistants"] = {k: v for k, v in assistants_env.items() if v}

    # Канали Telegram
    telegram_channels_env = {
        "uk": os.getenv("TELEGRAM_CHANNEL_ID_UK"),
        "en": os.getenv("TELEGRAM_CHANNEL_ID_EN"),
        "de": os.getenv("TELEGRAM_CHANNEL_ID_DE")
    }
    config["telegram_channels"] = {k: v for k, v in telegram_channels_env.items() if v}

    # Якщо хоча б один ключ задано в ENV, повертаємо його (може бути частковим)
    if any(config.values()) or config["assistants"] or config["telegram_channels"]:
        return config

    # Якщо ENV порожні — читаємо з config.json
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    raise FileNotFoundError("Не знайдено config.json або ENV змінних")

