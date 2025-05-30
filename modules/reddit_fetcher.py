import requests
import json
import os
from modules.config_loader import load_config

def fetch_reddit_posts(query="Google", limit=5):
    config = load_config()
    api_key = config.get("serpapi_key")
    if not api_key:
        raise ValueError("SerpAPI key not found in config")

    params = {
        "engine": "reddit",
        "q": query,
        "api_key": api_key
    }

    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()

    posts = []
    for post in data.get("organic_results", [])[:limit]:
        posts.append({
            "title": post.get("title"),
            "link": post.get("link"),
            "snippet": post.get("snippet")
        })

    return posts

if __name__ == "__main__":
    posts = fetch_reddit_posts()
    for post in posts:
        print("\nTitle:", post["title"])
        print("Link:", post["link"])
        print("Snippet:", post["snippet"])
