from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date

from .forms import CustomLoginForm
from profile_app.models import UserProfile
from achievements.models import DisplayedAchievement


def landing_view(request):
    if request.user.is_authenticated:
        return redirect('login:home')
    return render(request, 'login/landing.html')


def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                messages.success(request, "Добро пожаловать!")
                return redirect('login:home')
            else:
                messages.error(request, "Неверный логин или пароль.")
    else:
        form = CustomLoginForm()
    return render(request, 'login/login.html', {'form': form})


@login_required
def home_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    context = {
        'is_student': profile.is_student() if profile else False,
        'is_teacher': profile.is_teacher() if profile else False,
        'profile': profile,
    }

    if profile and profile.is_student():
        context['displayed_achievements'] = DisplayedAchievement.objects.filter(
            user=user).select_related('achievement')
        age = None
        if profile.birth_date:
            today = date.today()
            age = today.year - profile.birth_date.year - (
                (today.month, today.day) < (profile.birth_date.month, profile.birth_date.day))
        context['age'] = age

    return render(request, 'login/home.html', context)
