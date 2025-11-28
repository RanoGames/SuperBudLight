# login/views.py
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .forms import CustomLoginForm, StudentProfileEditForm, AwardPointsForm
from .models import UserProfile, Group, ACTIVITY_TITLES, ACTIVITY_MAX_POINTS, ARTEL_CHOICES, Achievement, UserAchievement, DisplayedAchievement


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
    role = getattr(request.user, 'profile', None) and request.user.profile.role
    return render(request, 'login/home.html', {'role': role})


@login_required
def profile_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    if not profile:
        messages.error(request, "Профиль не найден.")
        return redirect('login:home')

    context = {
        'user': user,
        'profile': profile,
        'max_points': ACTIVITY_MAX_POINTS,
    }

    if profile.role == 'teacher':
        managed_groups = Group.objects.filter(teacher=user)
        context['managed_groups'] = managed_groups

    elif profile.role == 'student':
        # Подготавливаем данные для прогресс-баров
        activity_data = []
        for key, label in ACTIVITY_TITLES.items():
            points = getattr(profile, f"{key}_points")
            percent = int((points / ACTIVITY_MAX_POINTS) * 100) if ACTIVITY_MAX_POINTS > 0 else 0
            activity_data.append((label, points, percent))
        context['activity_data'] = activity_data
    displayed_achievements = DisplayedAchievement.objects.filter(
        user=user
    ).select_related('achievement')

    context['displayed_achievements'] = displayed_achievements

    return render(request, 'login/profile.html', context)


@login_required
def teacher_students_view(request):
    if not (hasattr(request.user, 'profile') and request.user.profile.role == 'teacher'):
        raise PermissionDenied("Только педагоги могут просматривать этот раздел.")

    managed_groups = Group.objects.filter(teacher=request.user)
    students = UserProfile.objects.filter(
        role='student',
        group__in=managed_groups
    ).select_related('user', 'group')

    return render(request, 'login/teacher_students.html', {'students': students})


@login_required
@login_required
def edit_student_view(request, student_id):
    if not (hasattr(request.user, 'profile') and request.user.profile.role == 'teacher'):
        raise PermissionDenied("Только педагоги могут редактировать учеников.")

    student_profile = get_object_or_404(UserProfile, id=student_id, role='student')

    if not student_profile.group or student_profile.group.teacher != request.user:
        raise PermissionDenied("Вы не можете редактировать этого ученика.")

    if request.method == 'POST':
        form = StudentProfileEditForm(request.POST, instance=student_profile, teacher_user=request.user)
        if form.is_valid():
            student_profile = form.save()
            student_profile.update_rank_if_needed()  # ← ключевая строка
            messages.success(request, f"Профиль {student_profile.user.username} успешно обновлён.")
            return redirect('login:teacher_students')
    else:
        form = StudentProfileEditForm(instance=student_profile, teacher_user=request.user)

    return render(request, 'login/edit_student.html', {
        'form': form,
        'student': student_profile.user
    })


@login_required
def award_points_view(request):
    if not (hasattr(request.user, 'profile') and request.user.profile.role == 'teacher'):
        raise PermissionDenied("Только педагоги могут начислять очки.")

    if request.method == 'POST':
        form = AwardPointsForm(request.POST, teacher_user=request.user)
        if form.is_valid():
            student_profile = form.cleaned_data['student']
            activity = form.cleaned_data['activity']
            points = form.cleaned_data['points']

            current = getattr(student_profile, f"{activity}_points")
            new_value = min(current + points, ACTIVITY_MAX_POINTS)
            setattr(student_profile, f"{activity}_points", new_value)
            student_profile.save(update_fields=[f"{activity}_points"])

            student_profile.update_rank_if_needed()

            messages.success(
                request,
                f"Ученику {student_profile.user.username} начислено {points} очков в категории «{dict(form.ACTIVITY_CHOICES)[activity]}»."
            )
            return redirect('login:award_points')
    else:
        form = AwardPointsForm(teacher_user=request.user)

    return render(request, 'login/award_points.html', {'form': form})

@login_required
def rating_view(request):
    students = UserProfile.objects.filter(role='student').order_by('-rating_points')

    top_300 = []
    current_user_rank = None

    for index, student in enumerate(students, start=1):
        if student.user == request.user:
            current_user_rank = index
        if index <= 300:
            top_300.append((index, student))
    context = {
        'top_300': top_300,
        'current_user_profile': request.user.profile,
        'current_user_rank': current_user_rank,
    }

    return render(request, 'login/rating.html', context)

@login_required
def artel_rating_view(request):
    # Сумма рейтинговых баллов участников каждого артеля
    ratings = (
    UserProfile.objects
    .exclude(artel__isnull=True)
    .exclude(artel='')
    .values('artel')
    .annotate(total_points=Sum('rating_points'))
    .order_by('-total_points')
)


    # Преобразуем machine-name → русское название
    artel_verbose = dict(ARTEL_CHOICES)

    for item in ratings:
        item['artel_name'] = artel_verbose.get(item['artel'], item['artel'])

    return render(request, 'login/artel_rating.html', {
        'ratings': ratings
    })


from .forms import AchievementForm
from django.conf import settings
import os

# === Учитель: управление достижениями ===
@login_required
def manage_achievements_view(request):
    if not (hasattr(request.user, 'profile') and request.user.profile.role == 'teacher'):
        raise PermissionDenied("Только педагоги могут управлять достижениями.")

    if request.method == 'POST':
        form = AchievementForm(request.POST, request.FILES)
        if form.is_valid():
            achievement = form.save(commit=False)
            achievement.created_by = request.user
            achievement.save()
            messages.success(request, f"Достижение «{achievement.name}» успешно создано!")
            return redirect('login:manage_achievements')
    else:
        form = AchievementForm()

    achievements = Achievement.objects.all()
    return render(request, 'login/manage_achievements.html', {
        'form': form,
        'achievements': achievements
    })


# === Ученик: все достижения ===
@login_required
def achievements_catalog_view(request):
    # Все доступные достижения
    all_achievements = Achievement.objects.all()

    # Полученные достижения текущего пользователя
    earned_ids = set(
        UserAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True)
    )

    # Достижения, отображаемые в профиле
    displayed_ids = set(
        DisplayedAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True)
    )

    context = {
        'achievements': all_achievements,
        'earned_ids': earned_ids,
        'displayed_ids': displayed_ids,
    }
    return render(request, 'login/achievements_catalog.html', context)


# === AJAX: добавить/убрать из отображаемых ===
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
@login_required
def toggle_displayed_achievement(request):
    achievement_id = request.POST.get('achievement_id')
    action = request.POST.get('action')  # 'add' или 'remove'

    try:
        achievement = Achievement.objects.get(id=achievement_id)
        user_earned = UserAchievement.objects.filter(user=request.user, achievement=achievement).exists()
        if not user_earned:
            return JsonResponse({'error': 'Вы не получили это достижение'}, status=403)

        if action == 'add':
            DisplayedAchievement.objects.get_or_create(user=request.user, achievement=achievement)
        elif action == 'remove':
            DisplayedAchievement.objects.filter(user=request.user, achievement=achievement).delete()

        return JsonResponse({'success': True})
    except Achievement.DoesNotExist:
        return JsonResponse({'error': 'Достижение не найдено'}, status=404)