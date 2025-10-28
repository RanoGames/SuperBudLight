from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomLoginForm

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
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
    # Получаем роль пользователя, если профиль существует
    role = None
    if hasattr(request.user, 'profile'):
        role = request.user.profile.role

    return render(request, 'login/home.html', {'role': role})