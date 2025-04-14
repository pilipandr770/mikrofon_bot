import requests
from modules.config_loader import load_config

def send_telegram(text, image_path):
    config = load_config()
    token = config.get("telegram_token")
    chat_id = config.get("telegram_channel_id")

    if not token or not chat_id:
        print("Telegram token or channel ID not found in config.")
        return

    # Ограничиваем длину подписи до 1024 символов (лимит Telegram)
    caption = text[:1024] if len(text) > 1024 else text
    
    # Надсилаємо фото з підписом
    with open(image_path, "rb") as img:
        files = {"photo": img}
        data = {
            "chat_id": chat_id,
            "caption": caption,
            "parse_mode": "HTML"
        }
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        response = requests.post(url, data=data, files=files)

    if response.status_code == 200:
        print("✅ Telegram: Post sent successfully.")
        
        # Если текст был обрезан, отправляем остальную часть как текстовое сообщение
        if len(text) > 1024:
            # Разбиваем остаток текста на части по 4096 символов (максимальная длина текстового сообщения в Telegram)
            remainder = text[1024:]
            chunk_size = 4096
            
            for i in range(0, len(remainder), chunk_size):
                chunk = remainder[i:i + chunk_size]
                data = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML"
                }
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                response = requests.post(url, data=data)
                if response.status_code != 200:
                    print(f"❌ Telegram: Failed to send text chunk. Status code: {response.status_code}")
                    print(response.text)
    else:
        print(f"❌ Telegram: Failed to send post. Status code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    with open("output/article_de.txt", "r", encoding="utf-8") as f:
        german_text = f.read()

    image_path = "output/image.png"
    send_telegram(german_text, image_path)
