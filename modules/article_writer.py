import json
import os
import asyncio
from openai import OpenAI
from modules.reddit_fetcher import fetch_reddit_posts
from modules.config_loader import load_config


async def generate_article(entry):
    """Генерация статьи на основе записи из RSS"""
    config = load_config()
    client = OpenAI(api_key=config["openai_api_key"])

    source = entry["source"]
    title = entry["title"]
    summary = entry["summary"]
    
    # Получаем обсуждения с Reddit в зависимости от источника статьи
    reddit_posts = fetch_reddit_posts(source.title(), limit=3)
    reddit_summary = "\n".join([f"- {p['title']}: {p['snippet']}" for p in reddit_posts])

    # Формируем запрос в зависимости от источника
    user_input = f"""
    Напиши цікаву, коротку статтю на основі цієї публікації {source.title()}:
    Title: {title}
    Summary: {summary}

    Також врахуй обговорення на Reddit:
    {reddit_summary}

    В кінці додай:
    1. 2-3 приклади застосування для малого та середнього бізнесу
    2. Заклик спробувати нашого AI-асистента для сайтів
    """

    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=config["assistant_id"]
    )

    print(f"Waiting for assistant to respond for {source} article...")
    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run.status == "completed":
            break
        elif run.status == "failed":
            raise Exception("Assistant run failed")
        await asyncio.sleep(2)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    content = messages.data[0].content[0].text.value

    # Создаем директорию для сохранения статей по источнику
    source_dir = os.path.join("output", source)
    os.makedirs(source_dir, exist_ok=True)
    
    # Создаем уникальное имя файла на основе ID статьи
    file_id = entry["id"].split("/")[-2] if "/" in entry["id"] else entry["id"]
    article_file = os.path.join(source_dir, f"article_{file_id}.txt")
    
    # Сохраняем результат
    with open(article_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Article for {source} saved to {article_file}")
    
    return article_file, content

if __name__ == "__main__":
    from modules.rss_reader import get_next_publication
    
    entry = get_next_publication()
    if entry:
        asyncio.run(generate_article(entry))
    else:
        print("No entries in the queue to process.")
