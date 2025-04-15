import os
import json
import time
from openai import OpenAI
from modules.config_loader import load_config

PLAN_DIR = "output"

def load_today_plan():
    today = time.strftime("%Y-%m-%d")
    path = os.path.join(PLAN_DIR, f"plan_{today}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Не знайдено план на {today}: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), path

def save_plan(plan, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

def generate_post_and_prompt(title, idea):
    config = load_config()
    client = OpenAI(api_key=config["openai_api_key"])

    user_prompt = f"""
    На основі ідеї для публікації створи короткий, логічно завершений пост для соцмереж (до 1000 символів), і промпт для генерації ілюстрації в стилі DALL·E 3.

    Формат відповіді:
    ### TEXT ###
    <текст публікації>
    ### IMAGE_PROMPT ###
    <короткий опис зображення>

    Ідея: {idea}
    Заголовок: {title}
    """

    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_prompt
    )
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=config["assistants"]["writer"]
    )

    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        if run.status == "completed":
            break
        elif run.status == "failed":
            raise Exception("Assistant run failed")
        time.sleep(2)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    content = messages.data[0].content[0].text.value

    if "### TEXT ###" in content and "### IMAGE_PROMPT ###" in content:
        text_part = content.split("### TEXT ###")[1].split("### IMAGE_PROMPT ###")[0].strip()
        prompt_part = content.split("### IMAGE_PROMPT ###")[1].strip()
        return text_part, prompt_part
    else:
        raise ValueError("Невірний формат відповіді GPT")

def fill_plan_with_content(plan):
    """
    Заполняет план контентом для всех постов со статусом 'empty'.
    """
    for i, post in enumerate(plan["posts"]):
        if post["status"] != "empty":
            continue
        print(f"✍️ Генеруємо публікацію {i+1}: {post['title']}")
        try:
            text, image_prompt = generate_post_and_prompt(post["title"], post["idea"])
            post["text"] = text
            post["image_prompt"] = image_prompt
            post["status"] = "filled"
            print("✅ Успішно")
        except Exception as e:
            print(f"❌ Помилка при генерації: {e}")
            post["status"] = "error"
    print("📘 План оновлено")
    return plan

if __name__ == "__main__":
    plan, path = load_today_plan()
    updated_plan = fill_plan_with_content(plan)
    save_plan(updated_plan, path)
