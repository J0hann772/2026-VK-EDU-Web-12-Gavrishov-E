from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag


class EmptyDatabasePagesTest(TestCase):
    def test_empty_index_and_hot_pages(self):
        response = self.client.get(reverse('questions:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пока нет ни одного вопроса')
        self.assertContains(response, 'Тегов пока нет')
        self.assertContains(response, 'Пользователей пока нет')

        response = self.client.get(reverse('questions:hot'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пока нет ни одного популярного вопроса')

    def test_empty_tag_and_empty_question_answers(self):
        tag = Tag.objects.create(name='python')
        response = self.client.get(tag.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'По этому тегу пока нет ни одного вопроса')

        user = User.objects.create_user(username='author1', password='secret')
        question = Question.objects.create(title='Тестовый вопрос', text='Текст', author=user)
        response = self.client.get(question.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пока нет ни одного ответа к этому вопросу')

    def test_404_pages(self):
        self.assertEqual(self.client.get('/question/999999/').status_code, 404)
        self.assertEqual(self.client.get('/question/abc/').status_code, 404)
        self.assertEqual(self.client.get('/tag/nonexistent-tag/').status_code, 404)


class ModelsAndLikesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret')
        self.profile = Profile.objects.create(user=self.user, nickname='Тестер')
        self.tag = Tag.objects.create(name='django')
        self.q1 = Question.objects.create(title='Первый', text='Текст 1', author=self.user)
        self.q2 = Question.objects.create(title='Второй', text='Текст 2', author=self.user)
        self.q1.tags.add(self.tag)
        self.answer = Answer.objects.create(question=self.q1, author=self.user, text='Ответ 1')

    def test_question_like_unique_together_and_rating(self):
        like = QuestionLike.objects.create(user=self.user, question=self.q1, value=QuestionLike.LIKE)
        self.q1.refresh_from_db()
        self.assertEqual(self.q1.rating, 1)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                QuestionLike.objects.create(user=self.user, question=self.q1, value=QuestionLike.LIKE)

        like.delete()
        self.q1.refresh_from_db()
        self.assertEqual(self.q1.rating, 0)

    def test_answer_like_unique_together_and_rating(self):
        AnswerLike.objects.create(user=self.user, answer=self.answer, value=AnswerLike.DISLIKE)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.rating, -1)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AnswerLike.objects.create(user=self.user, answer=self.answer, value=AnswerLike.LIKE)

    def test_managers_ordering(self):
        QuestionLike.objects.create(user=self.user, question=self.q1, value=QuestionLike.LIKE)

        new_list = list(Question.objects.new())
        self.assertEqual([q.pk for q in new_list], [self.q2.pk, self.q1.pk])

        hot_list = list(Question.objects.hot())
        self.assertEqual([q.pk for q in hot_list], [self.q1.pk, self.q2.pk])

        tag_list = list(Question.objects.by_tag('django'))
        self.assertEqual([q.pk for q in tag_list], [self.q1.pk])


class FillDbAndPerformanceTest(TestCase):
    def test_fill_db_counts_and_no_n_plus_one(self):
        out = StringIO()
        call_command('fill_db', 5, stdout=out)

        self.assertEqual(User.objects.count(), 5)
        self.assertEqual(Profile.objects.count(), 5)
        self.assertEqual(Tag.objects.count(), 5)
        self.assertEqual(Question.objects.count(), 50)
        self.assertEqual(Answer.objects.count(), 500)
        self.assertEqual(QuestionLike.objects.count() + AnswerLike.objects.count(), 1000)

        # Проверяем, что количество SQL-запросов на страницах константное (нет N+1)
        with CaptureQueriesContext(connection) as ctx_index:
            resp = self.client.get(reverse('questions:index'))
            self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(len(ctx_index), 6)

        with CaptureQueriesContext(connection) as ctx_hot:
            resp = self.client.get(reverse('questions:hot'))
            self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(len(ctx_hot), 6)

        first_tag = Tag.objects.first()
        with CaptureQueriesContext(connection) as ctx_tag:
            resp = self.client.get(first_tag.get_absolute_url())
            self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(len(ctx_tag), 7)

        first_question = Question.objects.first()
        with CaptureQueriesContext(connection) as ctx_question:
            resp = self.client.get(first_question.get_absolute_url())
            self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(len(ctx_question), 7)

        # Проверка пагинации с некорректными параметрами
        self.assertEqual(self.client.get('/?page=abc').status_code, 200)
        self.assertEqual(self.client.get('/?page=9999').status_code, 200)
        self.assertEqual(self.client.get('/?page=-5').status_code, 200)

    def test_admin_pages_and_inlines(self):
        call_command('fill_db', 2, stdout=StringIO())
        admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.client.force_login(admin_user)

        question = Question.objects.first()
        urls = [
            '/admin/',
            '/admin/auth/user/',
            f'/admin/auth/user/{admin_user.pk}/change/',
            '/admin/core/profile/',
            '/admin/questions/tag/',
            '/admin/questions/question/',
            f'/admin/questions/question/{question.pk}/change/',
            '/admin/questions/answer/',
            '/admin/questions/questionlike/',
            '/admin/questions/answerlike/',
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f'Ошибка на {url}')
