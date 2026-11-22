from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from django.templatetags.static import static
from django.urls import reverse


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('questions:tag', kwargs={'tag_name': self.name})


class QuestionManager(models.Manager):
    def with_related(self):
        # Подсчёт ответов подзапросом выполняется только для выбранных вопросов на странице
        answers_subquery = (
            Answer.objects.filter(question=OuterRef('pk'))
            .values('question')
            .annotate(total=Count('id'))
            .values('total')
        )
        return (
            self.get_queryset()
            .select_related('author', 'author__profile')
            .prefetch_related('tags')
            .annotate(
                answers_count=Coalesce(
                    Subquery(answers_subquery, output_field=models.IntegerField()),
                    0,
                )
            )
        )

    def new(self):
        return self.with_related().order_by('-created_at', '-id')

    def hot(self):
        return self.with_related().order_by('-rating', '-created_at', '-id')

    def by_tag(self, tag):
        if isinstance(tag, Tag):
            return self.with_related().filter(tags=tag).order_by('-created_at', '-id')
        return self.with_related().filter(tags__name=tag).order_by('-created_at', '-id')


class Question(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name='Заголовок',
    )
    text = models.TextField(
        verbose_name='Текст вопроса',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Автор',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='questions',
        blank=True,
        verbose_name='Теги',
    )
    rating = models.IntegerField(
        default=0,
        db_index=True,
        verbose_name='Рейтинг',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата создания',
    )

    objects = QuestionManager()

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ('-created_at', '-id')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('questions:question', kwargs={'question_id': self.pk})

    def get_author_name(self):
        profile = getattr(self.author, 'profile', None)
        if profile and profile.nickname:
            return profile.nickname
        return self.author.username

    def get_author_avatar_url(self):
        profile = getattr(self.author, 'profile', None)
        if profile and profile.avatar:
            return profile.avatar.url
        return static('core/img/author1.png')


class AnswerManager(models.Manager):
    def for_question(self, question):
        return (
            self.get_queryset()
            .filter(question=question)
            .select_related('author', 'author__profile')
            .order_by('-is_correct', '-rating', 'created_at', 'id')
        )


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Вопрос',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Автор',
    )
    text = models.TextField(
        verbose_name='Текст ответа',
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name='Правильный ответ',
    )
    rating = models.IntegerField(
        default=0,
        db_index=True,
        verbose_name='Рейтинг',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата создания',
    )

    objects = AnswerManager()

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'
        ordering = ('-is_correct', '-rating', 'created_at', 'id')

    def __str__(self):
        return f'Ответ #{self.pk} на вопрос #{self.question_id}'

    def get_author_name(self):
        profile = getattr(self.author, 'profile', None)
        if profile and profile.nickname:
            return profile.nickname
        return self.author.username

    def get_author_avatar_url(self):
        profile = getattr(self.author, 'profile', None)
        if profile and profile.avatar:
            return profile.avatar.url
        return static('core/img/author1.png')


class QuestionLike(models.Model):
    LIKE = 1
    DISLIKE = -1
    VALUE_CHOICES = (
        (LIKE, 'Лайк'),
        (DISLIKE, 'Дизлайк'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='question_likes',
        verbose_name='Пользователь',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Вопрос',
    )
    value = models.SmallIntegerField(
        choices=VALUE_CHOICES,
        default=LIKE,
        verbose_name='Оценка',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        verbose_name = 'Лайк вопроса'
        verbose_name_plural = 'Лайки вопросов'
        unique_together = ('user', 'question')

    def __str__(self):
        return f'{self.user} -> вопрос #{self.question_id} ({self.value})'

    def _update_question_rating(self):
        total = self.question.likes.aggregate(total=Sum('value'))['total'] or 0
        Question.objects.filter(pk=self.question_id).update(rating=total)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_question_rating()

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        self._update_question_rating()
        return result


class AnswerLike(models.Model):
    LIKE = 1
    DISLIKE = -1
    VALUE_CHOICES = (
        (LIKE, 'Лайк'),
        (DISLIKE, 'Дизлайк'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answer_likes',
        verbose_name='Пользователь',
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Ответ',
    )
    value = models.SmallIntegerField(
        choices=VALUE_CHOICES,
        default=LIKE,
        verbose_name='Оценка',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        verbose_name = 'Лайк ответа'
        verbose_name_plural = 'Лайки ответов'
        unique_together = ('user', 'answer')

    def __str__(self):
        return f'{self.user} -> ответ #{self.answer_id} ({self.value})'

    def _update_answer_rating(self):
        total = self.answer.likes.aggregate(total=Sum('value'))['total'] or 0
        Answer.objects.filter(pk=self.answer_id).update(rating=total)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_answer_rating()

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        self._update_answer_rating()
        return result
