import random

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from faker import Faker

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag

BATCH_SIZE = 5000
UPDATE_BATCH_SIZE = 2000


def distribute_likes(num_items, total_likes, max_per_item):
    """Распределяет total_likes по num_items объектам (не больше max_per_item на один)."""
    counts = [0] * num_items
    remaining = total_likes
    for i in range(num_items):
        items_left = num_items - i
        min_c = max(0, remaining - (items_left - 1) * max_per_item)
        avg = remaining / items_left
        max_c = min(max_per_item, remaining, max(min_c, int(avg * 2) + 1))
        c = remaining if items_left == 1 else random.randint(min_c, max_c)
        counts[i] = c
        remaining -= c
    return counts


class Command(BaseCommand):
    help = 'Наполняет базу данных тестовыми данными: python manage.py fill_db [ratio]'

    def add_arguments(self, parser):
        parser.add_argument(
            'ratio',
            type=int,
            help='Коэффициент заполнения базы (пользователей = ratio, вопросов = ratio*10 и т.д.)',
        )

    def handle(self, *args, **options):
        ratio = options['ratio']
        if ratio < 1:
            raise CommandError('Параметр ratio должен быть положительным целым числом.')

        fake = Faker('ru_RU')

        # Заранее готовим пулы фраз через Faker, чтобы не тормозить на миллионе записей
        self.stdout.write('Подготовка тестовых текстов (Faker)...')
        nicknames_pool = [fake.name() for _ in range(300)]
        titles_pool = [fake.sentence(nb_words=6).rstrip('.') + '?' for _ in range(300)]
        question_texts_pool = [fake.paragraph(nb_sentences=4) for _ in range(300)]
        answer_texts_pool = [fake.paragraph(nb_sentences=3) for _ in range(300)]
        tag_words_pool = [fake.word().lower() for _ in range(300)]

        user_ids = self._create_users(ratio, nicknames_pool)
        tag_ids = self._create_tags(ratio, tag_words_pool)
        question_ids = self._create_questions(ratio * 10, user_ids, tag_ids, titles_pool, question_texts_pool)
        answer_ids = self._create_answers(ratio * 100, user_ids, question_ids, answer_texts_pool)
        q_likes, a_likes = self._create_likes(ratio * 200, user_ids, question_ids, answer_ids)

        self.stdout.write(
            self.style.SUCCESS(
                f'Готово! Добавлено: пользователей={len(user_ids)}, тегов={len(tag_ids)}, '
                f'вопросов={len(question_ids)}, ответов={len(answer_ids)}, '
                f'оценок={q_likes + a_likes} (вопросам={q_likes}, ответам={a_likes}).'
            )
        )

    def _create_users(self, count, nicknames_pool):
        self.stdout.write(f'Создание пользователей и профилей ({count})...')
        # Хэшируем пароль один раз, чтобы не тратить время на тысячи хэширований
        password_hash = make_password('password123')
        start_num = User.objects.count() + 1

        user_ids = []
        users_batch = []
        for i in range(count):
            num = start_num + i
            users_batch.append(
                User(
                    username=f'user_{num}',
                    email=f'user_{num}@example.com',
                    password=password_hash,
                )
            )
            if len(users_batch) >= BATCH_SIZE:
                created = User.objects.bulk_create(users_batch, batch_size=BATCH_SIZE)
                user_ids.extend(u.pk for u in created)
                users_batch = []

        if users_batch:
            created = User.objects.bulk_create(users_batch, batch_size=BATCH_SIZE)
            user_ids.extend(u.pk for u in created)

        profiles_batch = []
        for uid in user_ids:
            profiles_batch.append(
                Profile(
                    user_id=uid,
                    nickname=random.choice(nicknames_pool)[:50],
                )
            )
            if len(profiles_batch) >= BATCH_SIZE:
                Profile.objects.bulk_create(profiles_batch, batch_size=BATCH_SIZE)
                profiles_batch = []

        if profiles_batch:
            Profile.objects.bulk_create(profiles_batch, batch_size=BATCH_SIZE)

        return user_ids

    def _create_tags(self, count, words_pool):
        self.stdout.write(f'Создание тегов ({count})...')
        used_names = set(Tag.objects.values_list('name', flat=True))
        tag_ids = []
        tags_batch = []

        for i in range(1, count + 1):
            word = random.choice(words_pool)[:35]
            name = word if word not in used_names else f'{word}_{i}'
            while name in used_names:
                name = f'{word}_{i}_{random.randint(10, 9999)}'
            used_names.add(name)
            tags_batch.append(Tag(name=name[:50]))

            if len(tags_batch) >= BATCH_SIZE:
                created = Tag.objects.bulk_create(tags_batch, batch_size=BATCH_SIZE)
                tag_ids.extend(t.pk for t in created)
                tags_batch = []

        if tags_batch:
            created = Tag.objects.bulk_create(tags_batch, batch_size=BATCH_SIZE)
            tag_ids.extend(t.pk for t in created)

        return tag_ids

    def _create_questions(self, count, user_ids, tag_ids, titles_pool, texts_pool):
        self.stdout.write(f'Создание вопросов ({count}) и привязка тегов...')
        question_ids = []
        questions_batch = []

        for i in range(1, count + 1):
            questions_batch.append(
                Question(
                    title=f'{random.choice(titles_pool)} (#{i})'[:255],
                    text=random.choice(texts_pool),
                    author_id=random.choice(user_ids),
                )
            )
            if len(questions_batch) >= BATCH_SIZE:
                created = Question.objects.bulk_create(questions_batch, batch_size=BATCH_SIZE)
                question_ids.extend(q.pk for q in created)
                questions_batch = []

        if questions_batch:
            created = Question.objects.bulk_create(questions_batch, batch_size=BATCH_SIZE)
            question_ids.extend(q.pk for q in created)

        # Связываем вопросы с тегами напрямую через промежуточную таблицу (bulk_create)
        through_model = Question.tags.through
        relations_batch = []
        max_tags = min(3, len(tag_ids))

        for qid in question_ids:
            chosen_tags = random.sample(tag_ids, random.randint(1, max_tags))
            for tid in chosen_tags:
                relations_batch.append(through_model(question_id=qid, tag_id=tid))
            if len(relations_batch) >= BATCH_SIZE:
                through_model.objects.bulk_create(relations_batch, batch_size=BATCH_SIZE)
                relations_batch = []

        if relations_batch:
            through_model.objects.bulk_create(relations_batch, batch_size=BATCH_SIZE)

        return question_ids

    def _create_answers(self, count, user_ids, question_ids, texts_pool):
        self.stdout.write(f'Создание ответов ({count})...')
        answer_ids = []
        answers_batch = []

        for i in range(count):
            answers_batch.append(
                Answer(
                    question_id=random.choice(question_ids),
                    author_id=random.choice(user_ids),
                    text=random.choice(texts_pool),
                    is_correct=(i % 10 == 0),
                )
            )
            if len(answers_batch) >= BATCH_SIZE:
                created = Answer.objects.bulk_create(answers_batch, batch_size=BATCH_SIZE)
                answer_ids.extend(a.pk for a in created)
                answers_batch = []

        if answers_batch:
            created = Answer.objects.bulk_create(answers_batch, batch_size=BATCH_SIZE)
            answer_ids.extend(a.pk for a in created)

        return answer_ids

    def _create_likes(self, total_likes, user_ids, question_ids, answer_ids):
        max_q_likes = len(user_ids) * len(question_ids)
        max_a_likes = len(user_ids) * len(answer_ids)

        q_likes_target = min(total_likes // 2, max_q_likes)
        a_likes_target = min(total_likes - q_likes_target, max_a_likes)

        self.stdout.write(f'Создание оценок вопросов ({q_likes_target})...')
        q_counts = distribute_likes(len(question_ids), q_likes_target, len(user_ids))
        q_likes_batch = []
        q_update_batch = []

        for qid, likes_cnt in zip(question_ids, q_counts):
            if likes_cnt == 0:
                continue
            chosen_users = random.sample(user_ids, likes_cnt)
            values = random.choices((1, -1), weights=(80, 20), k=likes_cnt)
            rating = sum(values)
            q_update_batch.append(Question(pk=qid, rating=rating))

            for uid, val in zip(chosen_users, values):
                q_likes_batch.append(QuestionLike(user_id=uid, question_id=qid, value=val))

            if len(q_likes_batch) >= BATCH_SIZE:
                QuestionLike.objects.bulk_create(q_likes_batch, batch_size=BATCH_SIZE)
                q_likes_batch = []
            if len(q_update_batch) >= UPDATE_BATCH_SIZE:
                Question.objects.bulk_update(q_update_batch, ['rating'], batch_size=UPDATE_BATCH_SIZE)
                q_update_batch = []

        if q_likes_batch:
            QuestionLike.objects.bulk_create(q_likes_batch, batch_size=BATCH_SIZE)
        if q_update_batch:
            Question.objects.bulk_update(q_update_batch, ['rating'], batch_size=UPDATE_BATCH_SIZE)

        self.stdout.write(f'Создание оценок ответов ({a_likes_target})...')
        a_counts = distribute_likes(len(answer_ids), a_likes_target, len(user_ids))
        a_likes_batch = []
        a_update_batch = []

        for aid, likes_cnt in zip(answer_ids, a_counts):
            if likes_cnt == 0:
                continue
            chosen_users = random.sample(user_ids, likes_cnt)
            values = random.choices((1, -1), weights=(80, 20), k=likes_cnt)
            rating = sum(values)
            a_update_batch.append(Answer(pk=aid, rating=rating))

            for uid, val in zip(chosen_users, values):
                a_likes_batch.append(AnswerLike(user_id=uid, answer_id=aid, value=val))

            if len(a_likes_batch) >= BATCH_SIZE:
                AnswerLike.objects.bulk_create(a_likes_batch, batch_size=BATCH_SIZE)
                a_likes_batch = []
            if len(a_update_batch) >= UPDATE_BATCH_SIZE:
                Answer.objects.bulk_update(a_update_batch, ['rating'], batch_size=UPDATE_BATCH_SIZE)
                a_update_batch = []

        if a_likes_batch:
            AnswerLike.objects.bulk_create(a_likes_batch, batch_size=BATCH_SIZE)
        if a_update_batch:
            Answer.objects.bulk_update(a_update_batch, ['rating'], batch_size=UPDATE_BATCH_SIZE)

        return q_likes_target, a_likes_target
