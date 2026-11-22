from django import forms

from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class AskForm(forms.ModelForm):
    tags = forms.CharField(
        label='Теги',
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control text-input-question',
                'placeholder': 'python, django, web',
            }
        ),
        help_text='Не больше 3 тегов, через запятую',
    )

    class Meta:
        model = Question
        fields = ('title', 'text')
        labels = {
            'title': 'Заголовок',
            'text': 'Текст вопроса',
        }
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control text-input-question',
                    'maxlength': 255,
                    'placeholder': 'How to create a Django project?',
                }
            ),
            'text': forms.Textarea(
                attrs={
                    'class': 'form-control text-input-question',
                    'rows': 5,
                    'placeholder': 'Опишите ваш вопрос подробнее...',
                }
            ),
        }

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if not title:
            raise forms.ValidationError('Заголовок не может быть пустым.')
        return title

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if not text:
            raise forms.ValidationError('Текст вопроса не может быть пустым.')
        return text

    def clean_tags(self):
        raw_tags = self.cleaned_data.get('tags', '')
        tags = []
        for item in raw_tags.split(','):
            name = item.strip()
            if not name:
                continue
            if len(name) > 50:
                raise forms.ValidationError(f'Тег «{name}» слишком длинный (максимум 50 символов).')
            if name not in tags:
                tags.append(name)

        if len(tags) > 3:
            raise forms.ValidationError('Можно указать не больше 3 тегов.')
        return tags

    def save(self, author, commit=True):
        question = super().save(commit=False)
        question.author = author
        if commit:
            question.save()
            tag_objects = []
            for tag_name in self.cleaned_data['tags']:
                tag_obj, _ = Tag.objects.get_or_create(name=tag_name)
                tag_objects.append(tag_obj)
            question.tags.set(tag_objects)
        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ('text',)
        labels = {
            'text': 'Ваш ответ',
        }
        widgets = {
            'text': forms.Textarea(
                attrs={
                    'class': 'user-answer-input form-control',
                    'rows': 4,
                    'maxlength': 2000,
                    'placeholder': 'Enter your answer here...',
                }
            ),
        }

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if not text:
            raise forms.ValidationError('Ответ не может быть пустым.')
        return text

    def save(self, question, author, commit=True):
        answer = super().save(commit=False)
        answer.question = question
        answer.author = author
        if commit:
            answer.save()
        return answer


class QuestionLikeForm(forms.Form):
    question_id = forms.IntegerField(min_value=1)
    value = forms.TypedChoiceField(
        choices=((QuestionLike.LIKE, 'like'), (QuestionLike.DISLIKE, 'dislike')),
        coerce=int,
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        self.question_obj = None
        self.existing_like = None
        super().__init__(*args, **kwargs)

    def clean_question_id(self):
        question_id = self.cleaned_data['question_id']
        question = Question.objects.filter(pk=question_id).first()
        if question is None:
            raise forms.ValidationError('Вопрос не найден.')
        self.question_obj = question
        return question_id

    def clean(self):
        cleaned_data = super().clean()
        if self.question_obj is None or self.user is None:
            return cleaned_data

        value = cleaned_data.get('value')
        existing = QuestionLike.objects.filter(user=self.user, question=self.question_obj).first()
        if existing and existing.value == value:
            raise forms.ValidationError('Вы уже поставили эту оценку.')
        self.existing_like = existing
        return cleaned_data

    def save(self):
        value = self.cleaned_data['value']
        if self.existing_like:
            self.existing_like.value = value
            self.existing_like.save()
        else:
            QuestionLike.objects.create(
                user=self.user,
                question=self.question_obj,
                value=value,
            )
        self.question_obj.refresh_from_db(fields=['rating'])
        return self.question_obj.rating


class AnswerLikeForm(forms.Form):
    answer_id = forms.IntegerField(min_value=1)
    value = forms.TypedChoiceField(
        choices=((AnswerLike.LIKE, 'like'), (AnswerLike.DISLIKE, 'dislike')),
        coerce=int,
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        self.answer_obj = None
        self.existing_like = None
        super().__init__(*args, **kwargs)

    def clean_answer_id(self):
        answer_id = self.cleaned_data['answer_id']
        answer = Answer.objects.filter(pk=answer_id).first()
        if answer is None:
            raise forms.ValidationError('Ответ не найден.')
        self.answer_obj = answer
        return answer_id

    def clean(self):
        cleaned_data = super().clean()
        if self.answer_obj is None or self.user is None:
            return cleaned_data

        value = cleaned_data.get('value')
        existing = AnswerLike.objects.filter(user=self.user, answer=self.answer_obj).first()
        if existing and existing.value == value:
            raise forms.ValidationError('Вы уже поставили эту оценку.')
        self.existing_like = existing
        return cleaned_data

    def save(self):
        value = self.cleaned_data['value']
        if self.existing_like:
            self.existing_like.value = value
            self.existing_like.save()
        else:
            AnswerLike.objects.create(
                user=self.user,
                answer=self.answer_obj,
                value=value,
            )
        self.answer_obj.refresh_from_db(fields=['rating'])
        return self.answer_obj.rating


class CorrectAnswerForm(forms.Form):
    question_id = forms.IntegerField(min_value=1)
    answer_id = forms.IntegerField(min_value=1)

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        self.question_obj = None
        self.answer_obj = None
        self.forbidden = False
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        question_id = cleaned_data.get('question_id')
        answer_id = cleaned_data.get('answer_id')
        if not question_id or not answer_id:
            return cleaned_data

        question = Question.objects.filter(pk=question_id).first()
        if question is None:
            raise forms.ValidationError('Вопрос не найден.')

        answer = Answer.objects.filter(pk=answer_id, question=question).first()
        if answer is None:
            raise forms.ValidationError('Ответ не найден для этого вопроса.')

        if self.user is None or question.author_id != self.user.pk:
            self.forbidden = True
            raise forms.ValidationError('Только автор вопроса может отмечать правильный ответ.')

        self.question_obj = question
        self.answer_obj = answer
        return cleaned_data

    def save(self):
        self.answer_obj.is_correct = not self.answer_obj.is_correct
        self.answer_obj.save(update_fields=['is_correct'])
        return self.answer_obj
