from django.urls import path

from . import views

app_name = 'questions'

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('tag/<str:tag_name>/', views.tag, name='tag'),
    path('question/<int:question_id>/', views.question, name='question'),
    path('ask/', views.ask, name='ask'),
    path('like/question/', views.like_question, name='like_question'),
    path('like/answer/', views.like_answer, name='like_answer'),
    path('answer/correct/', views.mark_correct_answer, name='mark_correct_answer'),
]
