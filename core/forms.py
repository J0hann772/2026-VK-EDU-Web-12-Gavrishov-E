from pathlib import Path

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import Profile

ALLOWED_AVATAR_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 МБ


def validate_avatar_file(avatar):
    if not avatar:
        return avatar

    ext = Path(avatar.name).suffix.lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        raise forms.ValidationError(
            'Недопустимый формат файла. Разрешены только: jpg, jpeg, png, webp.'
        )

    if avatar.size > MAX_AVATAR_SIZE:
        raise forms.ValidationError('Размер аватарки не должен превышать 2 МБ.')

    return avatar


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Логин',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите логин'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError('Неверный логин или пароль.')
            self.user = user

        return cleaned_data

    def get_user(self):
        return self.user


class SignupForm(forms.ModelForm):
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'dr.pepper@mail.ru'}),
    )
    nickname = forms.CharField(
        label='Никнейм',
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dr. Pepper'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
        help_text='Минимум 8 символов, не слишком простой и не только из цифр',
    )
    password_repeat = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите пароль'}),
    )
    avatar = forms.ImageField(
        label='Аватар',
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        help_text='Форматы: jpg, jpeg, png, webp. До 2 МБ.',
    )

    class Meta:
        model = User
        fields = ('username', 'email')
        labels = {
            'username': 'Логин',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'dr_pepper'}),
        }
        help_texts = {
            'username': 'До 150 символов: буквы, цифры и @/./+/-/_',
        }

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже используется.')
        return email

    def clean_avatar(self):
        return validate_avatar_file(self.cleaned_data.get('avatar'))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_repeat = cleaned_data.get('password_repeat')

        if password:
            temp_user = User(
                username=cleaned_data.get('username', ''),
                email=cleaned_data.get('email', ''),
            )
            try:
                validate_password(password, user=temp_user)
            except forms.ValidationError as error:
                self.add_error('password', error)

        if password and password_repeat and password != password_repeat:
            self.add_error('password_repeat', 'Пароли не совпадают.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                nickname=self.cleaned_data['nickname'].strip(),
                avatar=self.cleaned_data.get('avatar'),
            )
        return user


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Profile
        fields = ('nickname', 'avatar')
        labels = {
            'nickname': 'Никнейм',
            'avatar': 'Загрузить аватар',
        }
        widgets = {
            'nickname': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'avatar': 'Форматы: jpg, jpeg, png, webp. До 2 МБ.',
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if self.user is not None:
            self.fields['email'].initial = self.user.email

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError('Этот email уже занят другим пользователем.')
        return email

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        # Проверяем файл только если пользователь загрузил новый
        if avatar and hasattr(avatar, 'content_type'):
            validate_avatar_file(avatar)
        return avatar

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.nickname = (profile.nickname or '').strip()
        if commit:
            self.user.email = self.cleaned_data['email']
            self.user.save(update_fields=['email'])
            profile.save()
        return profile
