import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import requests

app = FastAPI()

# Получаем API ключи из переменных окружения
openai.api_key = os.environ.get("OPENAI_API_KEY")
newsapi_key = os.environ.get("NEWSAPI_KEY")

if not openai.api_key:
    raise ValueError("Переменная окружения OPENAI_API_KEY не установлена")
if not newsapi_key:
    raise ValueError("Переменная окружения NEWSAPI_KEY не установлена")

class Topic(BaseModel):
    topic: str

def get_recent_news(topic):
    url = "https://api.currentsapi.services/v1/latest-news"
    params = {
        "language": "en",
        "keywords": topic,
        "apiKey": newsapi_key
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных из CurrentsAPI: {response.text}")
    
    news_data = response.json().get("news", [])
    if not news_data:
        return "Свежих новостей не найдено."
    
    recent_news = [article["title"] for article in news_data[:3]]
    return "\n".join(recent_news)

def generate_post(topic):
    recent_news = get_recent_news(topic)

    # Генерация заголовка
    prompt_title = f"Придумайте привлекательный заголовок для поста на тему: {topic}"
    try:
        response_title = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_title}],
            max_tokens=50,
            n=1,
            temperature=0.7,
        )
        title = response_title.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации заголовка: {str(e)}")

    # Генерация мета-описания
    prompt_meta = f"Напишите краткое, но информативное мета-описание для поста с заголовком: {title}"
    try:
        response_meta = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_meta}],
            max_tokens=60,
            n=1,
            temperature=0.7,
        )
        meta_description = response_meta.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации мета-описания: {str(e)}")

    # Генерация контента поста
    prompt_post = (
        f"Напишите подробный и увлекательный пост для блога на тему: {topic}, учитывая следующие последние новости:\n"
        f"{recent_news}\n\n"
        "Используйте короткие абзацы, подзаголовки, примеры и ключевые слова для лучшего восприятия и SEO-оптимизации."
    )
    try:
        response_post = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt_post}],
            max_tokens=100,
            n=1,
            temperature=0.7,
        )
        post_content = response_post.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации контента поста: {str(e)}")

    return {
        "title": title,
        "meta_description": meta_description,
        "post_content": post_content
    }

@app.post("/generate-post")
async def generate_post_api(topic: Topic):
    generated_post = generate_post(topic.topic)
    return generated_post

@app.get("/")
async def root():
    return {"message": "Service is running"}

@app.get("/heartbeat")
async def heartbeat_api():
    return {"status": "OK"}

@app.head("/generate-post")
async def head_generate_post_api():
    return {"message": "This endpoint supports HEAD method."}  # Упрощенный ответ для HEAD метода

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)




