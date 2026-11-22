from django.shortcuts import get_object_or_404, render

from .models import Answer, Question, Tag
from .utils import paginate


def index(request):
    page = paginate(Question.objects.new(), request)
    return render(request, 'questions/index.html', {'page': page})


def hot(request):
    page = paginate(Question.objects.hot(), request)
    return render(request, 'questions/hot.html', {'page': page})


def tag(request, tag_name):
    tag_obj = get_object_or_404(Tag, name=tag_name)
    page = paginate(Question.objects.by_tag(tag_obj), request)
    return render(request, 'questions/tag.html', {'page': page, 'tag': tag_obj})


def question(request, question_id):
    one_question = get_object_or_404(Question.objects.with_related(), pk=question_id)
    page = paginate(Answer.objects.for_question(one_question), request, per_page=5)
    return render(request, 'questions/question.html', {'question': one_question, 'page': page})


def ask(request):
    return render(request, 'questions/ask.html')
