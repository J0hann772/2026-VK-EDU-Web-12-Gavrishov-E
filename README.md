# AskPupkin

Учебный проект курса «Web-разработка» (VK Education): сайт вопросов и ответов на Django, который строится по шагам, от статической вёрстки до полноценного приложения.

**Стек:** Python, Django, Bootstrap 5, Docker Compose.

Каждое домашнее задание живёт в своей ветке:

| Ветка | Задание | Что внутри |
|-------|---------|------------|
| `hw-1` | ДЗ 1 | статическая вёрстка на HTML и Bootstrap: главная, вопрос, создание вопроса, вход, регистрация |
| `hw-2` | ДЗ 2 | Django-проект: маршруты, шаблоны, пагинация, Docker Compose |

Сейчас в `main` лежит результат ДЗ 2. Данные пока не из базы, а заглушки в `questions/views.py`.

## Страницы

| URL | Имя маршрута | Страница |
|---|---|---|
| `/` | `questions:index` | новые вопросы |
| `/hot/` | `questions:hot` | лучшие вопросы |
| `/tag/<имя>/` | `questions:tag` | вопросы по тегу |
| `/question/<id>/` | `questions:question` | вопрос и ответы |
| `/ask/` | `questions:ask` | создание вопроса |
| `/login/` | `core:login` | вход |
| `/signup/` | `core:signup` | регистрация |
| `/profile/` | `core:profile` | настройки профиля |

## Структура

```
application/   настройки проекта (settings.py, urls.py)
core/          пользователи: вход, регистрация, профиль
questions/     вопросы: список, вопрос, создание
templates/     общие шаблоны (layouts/base.html, includes/)
manage.py
```

## Запуск

Локально:

```
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux, macOS
pip install -r requirements.txt
python manage.py runserver
```

Через Docker:

```
docker compose up --build
```

Сайт откроется на http://127.0.0.1:8000/

Переменные окружения: скопируйте `.env.example` в `.env` и поправьте значения.
Без `.env` используются значения по умолчанию.

## Заметки

Часть стилей написана вручную, чтобы разобраться, как это работает, остальное — Bootstrap.
