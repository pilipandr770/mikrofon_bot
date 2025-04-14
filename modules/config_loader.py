import os
import json

CONFIG_PATH = "config/config.json"

def load_config():
    config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)

    config["serpapi_key"] = os.getenv("SERPAPI_KEY", config.get("serpapi_key", ""))
    config["openai_api_key"] = os.getenv("OPENAI_API_KEY", config.get("openai_api_key", ""))
    config["assistant_id"] = os.getenv("ASSISTANT_ID", config.get("assistant_id", ""))

    return config
