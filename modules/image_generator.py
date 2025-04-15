import os
from openai import OpenAI
from .config_loader import load_config

client = OpenAI(api_key=load_config()["openai_api_key"])

def generate_image_prompt(article_text, source_name):
    prompt = f"""
    Based on the following article about {source_name}, write a short prompt (max 1 sentence) for generating an engaging illustration. It should visually summarize the main idea of the article:

    {article_text}
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def create_image_from_prompt(prompt_text):
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt_text,
        size="1024x1024",
        quality="standard",
        n=1
    )
    image_url = response.data[0].url
    return image_url

def save_image_from_url(image_url, source_name, file_id):
    """Сохраняет изображение из URL в директорию источника с уникальным именем"""
    import requests
    
    # Создаем директорию для изображений по источнику
    source_dir = os.path.join("output", source_name)
    os.makedirs(source_dir, exist_ok=True)
    
    output_path = os.path.join(source_dir, f"image_{file_id}.png")
    
    response = requests.get(image_url)
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return output_path

def generate_and_save_image(article_text, source_name, file_id):
    """Генерирует и сохраняет изображение для статьи"""
    print(f"Generating image prompt for {source_name} article...")
    image_prompt = generate_image_prompt(article_text, source_name)
    print(f"Prompt: {image_prompt}")
    
    print(f"Creating image via DALL·E 3 for {source_name}...")
    image_url = create_image_from_prompt(image_prompt)
    
    image_path = save_image_from_url(image_url, source_name, file_id)
    print(f"Image saved to {image_path}")
    
    return image_path

def generate_images_from_plan(plan):
    """
    Генерирует изображения для всех постов с image_prompt, если изображение ещё не создано.
    Помечает посты как image_generated и добавляет путь к картинке.
    """
    for i, post in enumerate(plan["posts"]):
        if not post.get("image_prompt") or post.get("image_generated"):
            continue
        print(f"🖼 Генеруємо зображення для поста {i+1}...")
        try:
            image_url = create_image_from_prompt(post["image_prompt"])
            image_path = save_image_from_url(
                image_url,
                plan["source"],
                str(i+1).zfill(3)
            )
            post["image_generated"] = True
            post["image_path"] = image_path
            print(f"✅ Зображення збережено: {image_path}")
        except Exception as e:
            print(f"❌ Помилка при генерації зображення: {e}")
            post["image_generated"] = False
    return plan

if __name__ == "__main__":
    from modules.rss_reader import get_next_publication
    import sys
    
    entry = get_next_publication()
    if entry:
        source_dir = os.path.join("output", entry["source"])
        file_id = entry["id"].split("/")[-2] if "/" in entry["id"] else entry["id"]
        article_file = os.path.join(source_dir, f"article_{file_id}.txt")
        
        if os.path.exists(article_file):
            with open(article_file, "r", encoding="utf-8") as f:
                article_text = f.read()
            
            generate_and_save_image(article_text, entry["source"], file_id)
        else:
            print(f"Article file not found: {article_file}")
    else:
        print("No entries in the queue to process.")
