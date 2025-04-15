import os
import json
from openai import OpenAI
from modules.config_loader import load_config
from modules.rss_reader import load_publication_queue
from datetime import datetime


PLAN_DIR = "output"


def create_daily_plan(news_entries):
    """
    Використовує GPT, щоб створити контент-план на основі добірки новин
    """
    config = load_config()
    client = OpenAI(api_key=config["openai_api_key"])

    combined_summary = "\n\n".join(
        [f"Title: {entry['title']}\nSummary: {entry['summary']}" for entry in news_entries]
    )

    user_prompt = f"""
    Ти — досвідчений AI-копірайтер. На основі добірки новин про штучний інтелект сформуй план для 3-5 коротких публікацій у соцмережах на день.

    Кожна публікація повинна бути логічним продовженням попередньої і мати унікальну тему.
    Не пиши сам текст постів — лише план: заголовок і суть публікації.

    Формат:
    [
        {{"title": "...", "idea": "..."}},
        ...
    ]

    Новини:
    {combined_summary}
    """

    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_prompt
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=config["assistants"]["planner"]
    )

    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run.status == "completed":
            break
        elif run.status == "failed":
            raise Exception("Plan generation failed")
        import time
        time.sleep(2)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    content = messages.data[0].content[0].text.value
    
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        raise Exception("Не вдалося розпарсити відповідь GPT як JSON:", content)

    return parsed


def generate_publication_plan():
    entries = load_publication_queue()
    if not entries:
        print("Черга публікацій пуста")
        return

    today_str = datetime.today().strftime("%Y-%m-%d")
    plan = create_daily_plan(entries)

    plan_data = {
        "date": today_str,
        "source": "rss",
        "posts": [
            {"title": post["title"], "idea": post["idea"], "status": "empty"}
            for post in plan
        ]
    }

    os.makedirs(PLAN_DIR, exist_ok=True)
    out_path = os.path.join(PLAN_DIR, f"plan_{today_str}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan_data, f, ensure_ascii=False, indent=2)

    print(f"✅ План збережено до {out_path}")


if __name__ == "__main__":
    generate_publication_plan()
