# 2026-VK-EDU-Web-12-Gavrishov-E

Домашнее задание 2 — Django-сайт вопросов и ответов AskPupkin: view, маршруты, шаблоны, пагинация, Docker.
Данные пока не из базы, а заглушки в `questions/views.py`.

## Структура проекта

```
application/   - настройки проекта (settings.py, urls.py)
core/          - приложение пользователя (вход, регистрация, профиль)
questions/     - приложение с вопросами (список, вопрос, создание)
templates/     - общие шаблоны (layouts/base.html, includes/)
static/        - собранная статика (collectstatic)
media/         - файлы, загруженные пользователями
manage.py
```

## Страницы

| URL | имя маршрута | страница |
|---|---|---|
| `/` | `questions:index` | новые вопросы |
| `/hot/` | `questions:hot` | лучшие вопросы |
| `/tag/<имя>/` | `questions:tag` | вопросы по тегу |
| `/question/<id>/` | `questions:question` | вопрос и ответы |
| `/ask/` | `questions:ask` | создание вопроса |
| `/login/` | `core:login` | вход |
| `/signup/` | `core:signup` | регистрация |
| `/profile/` | `core:profile` | настройки профиля |

## Запуск локально

```
python -m venv .venv
.venv\Scripts\activate          (Windows)
source .venv/bin/activate        (Linux и macOS)
pip install -r requirements.txt
python manage.py runserver
```

Сайт откроется на http://127.0.0.1:8000/

## Запуск через Docker Compose

```
docker compose up --build
```

Сайт откроется на http://127.0.0.1:8000/

## Переменные окружения

В файле `.env.example` лежит пример. Чтобы задать свои значения, скопируйте его в `.env`
(Docker Compose сам прочитает этот файл). Если `.env` нет, используются значения по умолчанию.

## Заметки

Писал немного своих стилей, чтоб разобраться что это такое.
В основном использовал bootstrap.

Когда долго не получалось выровнять сетку сайта, использовал помощь ИИ в google.
