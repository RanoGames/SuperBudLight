# login/views.py
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import ShopCategory, ShopItem, Purchase
from django.conf import settings
import os

from .forms import (
    CustomLoginForm, StudentProfileEditForm, AwardPointsForm,
    AchievementForm, AssignAchievementForm
)
# Добавлены импорты ShopItem и Purchase
from .models import (
    UserProfile, Group, Achievement, UserAchievement, DisplayedAchievement,
    ShopItem, Purchase,
    ACTIVITY_TITLES, ACTIVITY_MAX_POINTS, ARTEL_CHOICES
)


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
        activity_data = []
        for key, label in ACTIVITY_TITLES.items():
            points = getattr(profile, f"{key}_points")
            percent = int((points / ACTIVITY_MAX_POINTS) * 100) if ACTIVITY_MAX_POINTS > 0 else 0
            activity_data.append((label, points, percent))
        context['activity_data'] = activity_data
    displayed_achievements = DisplayedAchievement.objects.filter(user=user).select_related('achievement')
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
            student_profile.update_rank_if_needed()
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
            points_to_add = form.cleaned_data['points']

            # 1. Получаем текущее значение очков в категории
            current_activity_points = getattr(student_profile, f"{activity}_points")

            # 2. Считаем новое значение (не больше максимума, например, 100)
            new_activity_points = min(current_activity_points + points_to_add, ACTIVITY_MAX_POINTS)

            # 3. Вычисляем РЕАЛЬНУЮ разницу (Delta)
            # Например, если было 95, а добавляем 10 (лимит 100), то реально добавится только 5.
            delta = new_activity_points - current_activity_points

            if delta > 0:
                # Обновляем очки категории
                setattr(student_profile, f"{activity}_points", new_activity_points)

                # Обновляем общий рейтинг
                student_profile.rating_points += delta

                # Обновляем баланс (на ту же сумму)
                student_profile.balance += delta

                # Сохраняем все изменения одним запросом
                student_profile.save()

                # Обновляем звание (ранг)
                student_profile.update_rank_if_needed()

                messages.success(
                    request,
                    f"Ученику {student_profile.user.username} начислено {delta} очков. "
                    f"Баланс пополнен на {delta} монет."
                )
            else:
                messages.warning(
                    request,
                    f"Очки не начислены: достигнут лимит ({ACTIVITY_MAX_POINTS}) в категории «{dict(form.ACTIVITY_CHOICES)[activity]}»."
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
    ratings = (
        UserProfile.objects
        .exclude(artel__isnull=True)
        .exclude(artel='')
        .values('artel')
        .annotate(total_points=Sum('rating_points'))
        .order_by('-total_points')
    )
    artel_verbose = dict(ARTEL_CHOICES)
    for item in ratings:
        item['artel_name'] = artel_verbose.get(item['artel'], item['artel'])

    return render(request, 'login/artel_rating.html', {'ratings': ratings})


@login_required
def my_artel_rating_view(request):
    # 1. Проверяем наличие профиля
    if not hasattr(request.user, 'profile'):
        messages.error(request, "Профиль не найден.")
        return redirect('login:home')

    user_profile = request.user.profile
    current_artel = user_profile.artel

    # 2. Проверка: назначена ли артель (работает и для учителя, и для ученика)
    if not current_artel:
        if user_profile.role == 'teacher':
            msg = "В вашем профиле не указана Артель. Укажите её в админке, чтобы видеть рейтинг."
        else:
            msg = "Вы не состоите ни в одной артели."

        messages.warning(request, msg)
        return redirect('login:home')

    # 3. Получаем список студентов этой артели
    # Учителя в рейтинг НЕ попадают (фильтр role='student'), но видят его.
    artel_students = (
        UserProfile.objects
        .filter(role='student', artel=current_artel)
        .select_related('user', 'group')  # Оптимизация запросов
        .order_by('-rating_points')
    )

    # 4. Формируем список с местами
    top_students = []
    current_user_rank = None

    for index, student in enumerate(artel_students, start=1):
        # Если смотрит ученик, запоминаем его место
        if student.user == request.user:
            current_user_rank = index

        # Можно вывести всех или ограничить топ-100
        top_students.append((index, student))

    context = {
        'artel_name': dict(ARTEL_CHOICES).get(current_artel, current_artel),
        'top_students': top_students,
        'current_user_rank': current_user_rank,
        'current_user_profile': user_profile,
    }

    return render(request, 'login/my_artel_rating.html', context)


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

    achievements = Achievement.objects.filter(created_by=request.user)
    return render(request, 'login/manage_achievements.html', {
        'form': form,
        'achievements': achievements
    })


@login_required
def edit_achievement_view(request, achievement_id):
    if not (hasattr(request.user, 'profile') and request.user.profile.role == 'teacher'):
        raise PermissionDenied("Только педагоги могут редактировать достижения.")

    achievement = get_object_or_404(Achievement, id=achievement_id, created_by=request.user)

    if request.method == 'POST':
        form = AchievementForm(request.POST, request.FILES, instance=achievement)
        if form.is_valid():
            form.save()
            messages.success(request, f"Достижение «{achievement.name}» успешно обновлено!")
            return redirect('login:manage_achievements')
    else:
        form = AchievementForm(instance=achievement)

    return render(request, 'login/edit_achievement.html', {'form': form, 'achievement': achievement})


@login_required
def delete_achievement_view(request, achievement_id):
    if not (hasattr(request.user, 'profile') and request.user.profile.role == 'teacher'):
        raise PermissionDenied("Только педагоги могут удалять достижения.")

    achievement = get_object_or_404(Achievement, id=achievement_id, created_by=request.user)

    if request.method == 'POST':
        achievement_name = achievement.name
        achievement.delete()
        messages.success(request, f"Достижение «{achievement_name}» удалено.")
        return redirect('login:manage_achievements')

    return render(request, 'login/delete_achievement.html', {'achievement': achievement})


@login_required
def achievements_catalog_view(request):
    all_achievements = Achievement.objects.all()
    earned_ids = set(
        UserAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True)
    )
    displayed_ids = set(
        DisplayedAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True)
    )
    return render(request, 'login/achievements_catalog.html', {
        'achievements': all_achievements,
        'earned_ids': earned_ids,
        'displayed_ids': displayed_ids,
    })


@require_POST
@login_required
def toggle_displayed_achievement(request):
    achievement_id = request.POST.get('achievement_id')
    action = request.POST.get('action')

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


@login_required
def assign_achievement_view(request):
    if not (hasattr(request.user, 'profile') and request.user.profile.role == 'teacher'):
        raise PermissionDenied("Только педагоги могут назначать достижения.")

    if request.method == 'POST':
        form = AssignAchievementForm(request.POST, teacher_user=request.user)
        if form.is_valid():
            student_profile = form.cleaned_data['student']
            achievement = form.cleaned_data['achievement']

            obj, created = UserAchievement.objects.get_or_create(
                user=student_profile.user,
                achievement=achievement
            )

            if created:
                messages.success(
                    request,
                    f"Достижение «{achievement.name}» успешно назначено ученику {student_profile.user.username}."
                )
            else:
                messages.info(
                    request,
                    f"Ученик {student_profile.user.username} уже имеет это достижение."
                )
            return redirect('login:assign_achievement')
    else:
        form = AssignAchievementForm(teacher_user=request.user)

    return render(request, 'login/assign_achievement.html', {'form': form})


# === НОВЫЕ VIEWS ДЛЯ МАГАЗИНА ===

@login_required
def shop_view(request):
    """Страница магазина с категориями"""

    # 1. Получаем все категории для меню
    categories = ShopCategory.objects.all()

    # 2. Получаем ID выбранной категории из URL (например, ?category=2)
    category_id = request.GET.get('category')

    # 3. Фильтруем товары
    items = ShopItem.objects.filter(is_available=True)
    if category_id:
        items = items.filter(category_id=category_id)

    # 4. История покупок
    my_purchases = Purchase.objects.filter(user=request.user).select_related('item')

    context = {
        'categories': categories,
        'active_category_id': int(category_id) if category_id else None,  # Чтобы подсветить кнопку
        'items': items,
        'my_purchases': my_purchases,
        'user_balance': request.user.profile.balance if hasattr(request.user, 'profile') else 0
    }
    return render(request, 'login/shop.html', context)


@login_required
@require_POST
def buy_item_view(request, item_id):
    """Обработка покупки товара"""
    # Проверка: только ученики могут покупать
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'student':
        messages.error(request, "Только ученики могут совершать покупки.")
        return redirect('login:shop')

    item = get_object_or_404(ShopItem, id=item_id, is_available=True)
    profile = request.user.profile

    if profile.balance >= item.price:
        # 1. Списываем средства
        profile.balance -= item.price
        profile.save(update_fields=['balance'])

        # 2. Создаем запись о покупке
        Purchase.objects.create(
            user=request.user,
            item=item,
            price_at_moment=item.price
        )

        messages.success(request, f"Вы успешно купили «{item.name}»!")
    else:
        messages.error(request, "Недостаточно средств для покупки.")

    return redirect('login:shop')

