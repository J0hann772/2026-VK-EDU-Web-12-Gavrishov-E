# AskPupkin

Учебный проект курса «Web-разработка» (VK Education): сайт вопросов и ответов на Django, который строится по шагам, от статической вёрстки до полноценного приложения.

**Стек:** Python, Django, PostgreSQL, Bootstrap 5, Docker Compose.

Каждое домашнее задание живёт в своей ветке:

| Ветка | Задание | Что внутри |
|-------|---------|------------|
| `hw-1` | ДЗ 1 | статическая вёрстка на HTML и Bootstrap: главная, вопрос, создание вопроса, вход, регистрация |
| `hw-2` | ДЗ 2 | Django-проект: маршруты, шаблоны, пагинация, Docker Compose |
| `hw-3` | ДЗ 3 | модели БД, PostgreSQL, django-admin, менеджеры, наполнение БД (`fill_db`), `django-debug-toolbar` |

## Модели

* `core.Profile` — профиль пользователя (связь 1-к-1 с `django.contrib.auth.models.User`, аватар и никнейм)
* `questions.Tag` — тег вопроса
* `questions.Question` — вопрос (со своим менеджером `QuestionManager`: `new()`, `hot()`, `by_tag()`)
* `questions.Answer` — ответ на вопрос (менеджер `AnswerManager`: `for_question()`)
* `questions.QuestionLike`, `questions.AnswerLike` — оценки вопросов и ответов с ограничением `unique_together` на уровне БД

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
| `/admin/` | — | панель администратора (на русском языке) |

## Переменные окружения

Скопируйте `.env.example` в два файла (оба добавлены в `.gitignore`):
* `.env.local` — для локального запуска (`DB_HOST=localhost`)
* `.env.docker` — для запуска через Docker Compose (`DB_HOST=db`)

## Запуск

### Через Docker Compose (рекомендуется)

```bash
docker compose up --build
```

Сайт откроется на http://127.0.0.1:8000/, админка — на http://127.0.0.1:8000/admin/.

Создать суперпользователя и наполнить базу тестовыми данными внутри контейнера:

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py fill_db 100
```

Для полного объёма по требованиям ДЗ 3:

```bash
docker compose exec web python manage.py fill_db 10000
```

### Локально (с PostgreSQL на localhost:5432)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux, macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py fill_db 100
python manage.py runserver
```

## Отладка

При `DEBUG=True` автоматически подключается `django-debug-toolbar` для проверки SQL-запросов и отсутствия проблемы N+1.
