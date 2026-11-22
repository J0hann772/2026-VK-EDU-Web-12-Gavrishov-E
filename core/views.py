from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import LoginForm, ProfileForm, SignupForm
from .models import Profile


def _get_safe_next_url(request, fallback='questions:index'):
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback


def login(request):
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.get_user())
        return redirect(_get_safe_next_url(request))
    return render(request, 'core/login.html', {'form': form, 'next': next_url})


def signup(request):
    form = SignupForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        auth_login(request, user)
        return redirect('questions:index')
    return render(request, 'core/signup.html', {'form': form})


@require_POST
def logout(request):
    auth_logout(request)
    return redirect(_get_safe_next_url(request))


@login_required
def profile(request):
    user_profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=user_profile,
        user=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Изменения успешно сохранены.')
        return redirect('core:profile')
    return render(request, 'core/profile.html', {'form': form, 'profile': user_profile})
