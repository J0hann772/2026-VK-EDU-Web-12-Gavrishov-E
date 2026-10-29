from django.shortcuts import render

def index(request):
    return render(request,'questions/index.html')

def base(request):
    return render(request,'layouts/base.html') # test

def question(request):
    return render(request,'questions/question.html')