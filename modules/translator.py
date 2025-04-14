from openai import OpenAI
from .config_loader import load_config
import os

client = OpenAI(api_key=load_config()["openai_api_key"])

def translate_text(text, target_language):
    prompt = f"""
    Translate the following article into {target_language}. Keep the tone professional and engaging:

    {text}
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

def translate_article_multilang(article_text, source_name, file_id):
    """Переводит статью на несколько языков и сохраняет их в директории источника"""
    source_dir = os.path.join("output", source_name)
    os.makedirs(source_dir, exist_ok=True)
    
    translations = {
        "uk": article_text,  # оригінал українською
        "en": translate_text(article_text, "English"),
        "de": translate_text(article_text, "German")
    }
    
    # Сохраняем переводы
    for lang, content in translations.items():
        translation_file = os.path.join(source_dir, f"article_{file_id}_{lang}.txt")
        with open(translation_file, "w", encoding="utf-8") as f:
            f.write(content)
    
    return translations

if __name__ == "__main__":
    from modules.rss_reader import get_next_publication
    
    entry = get_next_publication()
    if entry:
        source_dir = os.path.join("output", entry["source"])
        file_id = entry["id"].split("/")[-2] if "/" in entry["id"] else entry["id"]
        article_file = os.path.join(source_dir, f"article_{file_id}.txt")
        
        if os.path.exists(article_file):
            with open(article_file, "r", encoding="utf-8") as f:
                article_text = f.read()
            
            print(f"Translating article for {entry['source']}...")
            translations = translate_article_multilang(article_text, entry["source"], file_id)
            print("Translations completed and saved.")
        else:
            print(f"Article file not found: {article_file}")
    else:
        print("No entries in the queue to process.")
