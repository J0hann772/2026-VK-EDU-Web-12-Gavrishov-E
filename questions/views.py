from django.http import Http404
from django.shortcuts import render

from .utils import paginate

# Данные-заглушки (пока без базы данных)
TAGS = ['perl', 'python', 'TechnoPark', 'MySQL', 'django', 'Mail.Ru', 'Voloshin', 'Firefox']

QUESTIONS = []
for i in range(1, 30):
    QUESTIONS.append({
        'id': i,
        'title': 'Question ' + str(i),
        'text': 'Text of question ' + str(i),
        'tags': [TAGS[i % 8], TAGS[(i + 3) % 8]],
        'answers_count': i % 5,
    })

ANSWERS = []
for i in range(1, 13):
    ANSWERS.append({
        'id': i,
        'text': 'Text of answer ' + str(i),
    })


def index(request):
    page = paginate(QUESTIONS, request)
    return render(request, 'questions/index.html', {'page': page})


def hot(request):
    # "лучшие" вопросы пока просто в обратном порядке
    hot_questions = QUESTIONS[::-1]
    page = paginate(hot_questions, request)
    return render(request, 'questions/hot.html', {'page': page})


def tag(request, tag_name):
    tag_questions = []
    for question in QUESTIONS:
        if tag_name in question['tags']:
            tag_questions.append(question)

    page = paginate(tag_questions, request)
    return render(request, 'questions/tag.html', {'page': page, 'tag': tag_name})


def question(request, question_id):
    one_question = None
    for item in QUESTIONS:
        if item['id'] == question_id:
            one_question = item

    if one_question is None:
        raise Http404('Question not found')

    page = paginate(ANSWERS, request, 3)
    return render(request, 'questions/question.html', {'question': one_question, 'page': page})


def ask(request):
    return render(request, 'questions/ask.html')
