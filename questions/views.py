import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import AnswerForm, AnswerLikeForm, AskForm, CorrectAnswerForm, QuestionLikeForm
from .models import Answer, Question, Tag
from .utils import paginate

ANSWERS_PER_PAGE = 5


def _parse_ajax_data(request):
    if request.content_type == 'application/json':
        try:
            return json.loads(request.body.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return None
    return request.POST


def _first_form_error(form):
    for errors in form.errors.values():
        if errors:
            return str(errors[0])
    return 'Некорректные данные.'


def index(request):
    page = paginate(Question.objects.new(), request)
    Question.objects.attach_user_votes(page, request.user)
    return render(request, 'questions/index.html', {'page': page})


def hot(request):
    page = paginate(Question.objects.hot(), request)
    Question.objects.attach_user_votes(page, request.user)
    return render(request, 'questions/hot.html', {'page': page})


def tag(request, tag_name):
    tag_obj = get_object_or_404(Tag, name=tag_name)
    page = paginate(Question.objects.by_tag(tag_obj), request)
    Question.objects.attach_user_votes(page, request.user)
    return render(request, 'questions/tag.html', {'page': page, 'tag': tag_obj})


def question(request, question_id):
    one_question = get_object_or_404(Question.objects.with_related(), pk=question_id)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(question=one_question, author=request.user)
            return redirect(answer.get_page_url(per_page=ANSWERS_PER_PAGE))
    else:
        form = AnswerForm()

    Question.objects.attach_user_votes([one_question], request.user)
    page = paginate(Answer.objects.for_question(one_question), request, per_page=ANSWERS_PER_PAGE)
    Answer.objects.attach_user_votes(page, request.user)
    return render(
        request,
        'questions/question.html',
        {'question': one_question, 'page': page, 'form': form},
    )


@login_required
def ask(request):
    form = AskForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        new_question = form.save(author=request.user)
        return redirect(new_question.get_absolute_url())
    return render(request, 'questions/ask.html', {'form': form})


def like_question(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Разрешён только POST-запрос.'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Войдите в аккаунт, чтобы оценивать вопросы.', 'login_url': reverse('core:login')},
            status=401,
        )

    data = _parse_ajax_data(request)
    if data is None:
        return JsonResponse({'error': 'Некорректный JSON.'}, status=400)

    form = QuestionLikeForm(data, user=request.user)
    if not form.is_valid():
        return JsonResponse({'error': _first_form_error(form)}, status=400)

    rating = form.save()
    return JsonResponse({'rating': rating, 'user_vote': form.cleaned_data['value']})


def like_answer(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Разрешён только POST-запрос.'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Войдите в аккаунт, чтобы оценивать ответы.', 'login_url': reverse('core:login')},
            status=401,
        )

    data = _parse_ajax_data(request)
    if data is None:
        return JsonResponse({'error': 'Некорректный JSON.'}, status=400)

    form = AnswerLikeForm(data, user=request.user)
    if not form.is_valid():
        return JsonResponse({'error': _first_form_error(form)}, status=400)

    rating = form.save()
    return JsonResponse({'rating': rating, 'user_vote': form.cleaned_data['value']})


def mark_correct_answer(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Разрешён только POST-запрос.'}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse(
            {'error': 'Войдите в аккаунт, чтобы отмечать правильный ответ.', 'login_url': reverse('core:login')},
            status=401,
        )

    data = _parse_ajax_data(request)
    if data is None:
        return JsonResponse({'error': 'Некорректный JSON.'}, status=400)

    form = CorrectAnswerForm(data, user=request.user)
    if not form.is_valid():
        status_code = 403 if form.forbidden else 400
        return JsonResponse({'error': _first_form_error(form)}, status=status_code)

    answer = form.save()
    return JsonResponse({'answer_id': answer.pk, 'is_correct': answer.is_correct})
