# AskPupkin

Учебный проект курса «Web-разработка» (VK Education): сайт вопросов и ответов, который строится по шагам, от статической вёрстки до полноценного Django-приложения.

Каждое домашнее задание живёт в своей ветке, в `main` лежит описание проекта.

## Ветки

| Ветка | Задание | Что внутри |
|-------|---------|------------|
| `hw-1` | ДЗ 1 | статическая вёрстка на HTML и Bootstrap: главная, вопрос, создание вопроса, вход, регистрация |
| `hw-2` | ДЗ 2 | Django-проект: маршруты, шаблоны, пагинация, Docker Compose |

Дальше проект будет дорабатываться в следующих ветках по мере выполнения заданий.

## Стек

Python, Django, Bootstrap 5, Docker Compose.

## Как запустить

Код находится в ветках заданий. Для актуальной версии:

```
git checkout hw-2
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux, macOS
pip install -r requirements.txt
python manage.py runserver
```

Сайт откроется на http://127.0.0.1:8000/

Через Docker: `docker compose up --build`. Подробности — в README соответствующей ветки.
