from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from datetime import date

from .forms import (
    CustomLoginForm, StudentProfileEditForm, AwardPointsForm,
    AchievementForm, AssignAchievementForm, AvatarUploadForm
)
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
    user = request.user
    profile = getattr(user, 'profile', None)

    context = {
        'is_student': profile.is_student() if profile else False,
        'is_teacher': profile.is_teacher() if profile else False,
        'profile': profile,
    }

    if profile and profile.is_student():
        displayed = DisplayedAchievement.objects.filter(user=user).select_related('achievement')
        context['displayed_achievements'] = displayed
        age = None
        if profile.birth_date:
            today = date.today()
            age = today.year - profile.birth_date.year - (
                (today.month, today.day) < (profile.birth_date.month, profile.birth_date.day))
        context['age'] = age

    return render(request, 'login/home.html', context)


@login_required
def profile_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    if not profile:
        messages.error(request, "Профиль не найден.")
        return redirect('login:home')

    if request.method == 'POST':
        avatar_form = AvatarUploadForm(request.POST, request.FILES, instance=profile)
        if avatar_form.is_valid():
            avatar_form.save()
            messages.success(request, "Аватарка обновлена!")
            return redirect('login:profile')
    else:
        avatar_form = AvatarUploadForm(instance=profile)

    context = {
        'user': user,
        'profile': profile,
        'max_points': ACTIVITY_MAX_POINTS,
        'avatar_form': avatar_form,
    }

    if profile.is_teacher():
        managed_groups = Group.objects.filter(teacher=user)
        context['managed_groups'] = managed_groups

    elif profile.is_student():
        activity_data = []
        for key, label in ACTIVITY_TITLES.items():
            points = getattr(profile, f"{key}_points")
            percent = int((points / ACTIVITY_MAX_POINTS) * 100) if ACTIVITY_MAX_POINTS > 0 else 0
            activity_data.append((label, points, percent))
        context['activity_data'] = activity_data

        owned_frame_ids = Purchase.objects.filter(
            user=user, item__item_type='frame'
        ).values_list('item_id', flat=True)
        context['owned_frames'] = ShopItem.objects.filter(id__in=owned_frame_ids)

    context['displayed_achievements'] = DisplayedAchievement.objects.filter(
        user=user).select_related('achievement')

    return render(request, 'login/profile.html', context)


@login_required
@require_POST
def equip_frame_view(request):
    frame_id = request.POST.get('frame_id')
    action = request.POST.get('action')
    profile = request.user.profile

    if action == 'unequip':
        profile.active_frame = None
        profile.save(update_fields=['active_frame'])
        messages.info(request, "Рамка снята.")
    elif action == 'equip' and frame_id:
        if Purchase.objects.filter(user=request.user, item_id=frame_id).exists():
            frame = ShopItem.objects.get(id=frame_id)
            profile.active_frame = frame
            profile.save(update_fields=['active_frame'])
            messages.success(request, f"Рамка «{frame.name}» установлена!")
        else:
            messages.error(request, "Вы не купили эту рамку.")

    return redirect('login:profile')


def check_merch_access(user_profile):
    if not user_profile.is_student():
        return False

    top_100_ids = UserProfile.objects.filter(
        roles__name='student'
    ).order_by('-rating_points').values_list('id', flat=True)[:100]

    if user_profile.id in top_100_ids:
        return True

    if user_profile.artel:
        top_10_artel_ids = UserProfile.objects.filter(
            roles__name='student', artel=user_profile.artel
        ).order_by('-rating_points').values_list('id', flat=True)[:10]
        if user_profile.id in top_10_artel_ids:
            return True

    return False


@login_required
def shop_view(request):
    current_tab = request.GET.get('tab', 'cosmetic')
    items = ShopItem.objects.filter(is_available=True, item_type=current_tab)

    can_buy_merch = False
    if hasattr(request.user, 'profile'):
        can_buy_merch = check_merch_access(request.user.profile)

    my_purchases = Purchase.objects.filter(user=request.user).select_related('item')
    purchased_item_ids = my_purchases.values_list('item_id', flat=True)

    context = {
        'items': items,
        'current_tab': current_tab,
        'can_buy_merch': can_buy_merch,
        'my_purchases': my_purchases,
        'purchased_item_ids': purchased_item_ids,
        'user_balance': request.user.profile.balance if hasattr(request.user, 'profile') else 0,
    }
    return render(request, 'login/shop.html', context)


@login_required
@require_POST
def buy_item_view(request, item_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_student():
        messages.error(request, "Только ученики могут совершать покупки.")
        return redirect('login:shop')

    with transaction.atomic():
        item = get_object_or_404(ShopItem.objects.select_for_update(), id=item_id, is_available=True)
        profile = UserProfile.objects.select_for_update().get(user=request.user)

        if item.item_type == 'merch' and not check_merch_access(profile):
            messages.error(request, "Ошибка доступа! Мерч доступен только Топ-100 школы или Топ-10 артели.")
            return redirect(f"/shop/?tab={item.item_type}")

        if item.item_type == 'frame' and Purchase.objects.filter(user=request.user, item=item).exists():
            messages.warning(request, "У вас уже есть эта рамка!")
            return redirect(f"/shop/?tab={item.item_type}")

        if item.quantity <= 0:
            messages.error(request, "К сожалению, этот товар закончился.")
            return redirect(f"/shop/?tab={item.item_type}")

        if profile.balance >= item.price:
            profile.balance -= item.price
            profile.save(update_fields=['balance'])
            item.quantity -= 1
            item.save(update_fields=['quantity'])
            Purchase.objects.create(
                user=request.user, item=item, price_at_moment=item.price,
                status='completed' if item.item_type == 'frame' else 'pending'
            )
            messages.success(request, f"Вы купили «{item.name}»!")
        else:
            messages.error(request, "Недостаточно средств.")

    return redirect(f"/shop/?tab={item.item_type}")


@login_required
def teacher_students_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_teacher():
        raise PermissionDenied("Только педагоги могут просматривать этот раздел.")

    managed_groups = Group.objects.filter(teacher=request.user)
    students = UserProfile.objects.filter(
        roles__name='student', group__in=managed_groups
    ).select_related('user', 'group').distinct()

    return render(request, 'login/teacher_students.html', {'students': students})


@login_required
def edit_student_view(request, student_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_teacher():
        raise PermissionDenied("Только педагоги могут редактировать учеников.")

    student_profile = get_object_or_404(
        UserProfile.objects.filter(roles__name='student'), id=student_id
    )

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

    return render(request, 'login/edit_student.html', {'form': form, 'student': student_profile.user})


@login_required
def award_points_view(request):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_teacher():
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
            delta = new_value - current
            if delta > 0:
                student_profile.rating_points += delta
                student_profile.balance += delta
                student_profile.save()
                student_profile.update_rank_if_needed()
                messages.success(request, f"Начислено {delta} очков.")
            else:
                messages.warning(request, "Достигнут лимит очков.")
            return redirect('login:award_points')
    else:
        form = AwardPointsForm(teacher_user=request.user)

    return render(request, 'login/award_points.html', {'form': form})


@login_required
def rating_view(request):
    students = UserProfile.objects.filter(
        roles__name='student'
    ).order_by('-rating_points').distinct()

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
    ratings = UserProfile.objects.filter(
        roles__name='student'
    ).exclude(artel__isnull=True).exclude(artel='').values('artel').annotate(
        total_points=Sum('rating_points')
    ).order_by('-total_points')

    artel_verbose = dict(ARTEL_CHOICES)
    for item in ratings:
        item['artel_name'] = artel_verbose.get(item['artel'], item['artel'])
    return render(request, 'login/artel_rating.html', {'ratings': ratings})


@login_required
def my_artel_rating_view(request):
    if not hasattr(request.user, 'profile'):
        return redirect('login:home')
    user_profile = request.user.profile
    current_artel = user_profile.artel
    if not current_artel:
        messages.warning(request, "Артель не назначена.")
        return redirect('login:home')

    artel_students = UserProfile.objects.filter(
        roles__name='student', artel=current_artel
    ).select_related('user', 'group').order_by('-rating_points').distinct()

    top_students = []
    current_user_rank = None
    for index, student in enumerate(artel_students, start=1):
        if student.user == request.user:
            current_user_rank = index
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
    if request.method == 'POST':
        form = AchievementForm(request.POST, request.FILES)
        if form.is_valid():
            ach = form.save(commit=False)
            ach.created_by = request.user
            ach.save()
            return redirect('login:manage_achievements')
    else:
        form = AchievementForm()
    achievements = Achievement.objects.filter(created_by=request.user)
    return render(request, 'login/manage_achievements.html', {'form': form, 'achievements': achievements})


@login_required
def edit_achievement_view(request, achievement_id):
    ach = get_object_or_404(Achievement, id=achievement_id, created_by=request.user)
    if request.method == 'POST':
        form = AchievementForm(request.POST, request.FILES, instance=ach)
        if form.is_valid():
            form.save()
            return redirect('login:manage_achievements')
    else:
        form = AchievementForm(instance=ach)
    return render(request, 'login/edit_achievement.html', {'form': form, 'achievement': ach})


@login_required
def delete_achievement_view(request, achievement_id):
    ach = get_object_or_404(Achievement, id=achievement_id, created_by=request.user)
    if request.method == 'POST':
        ach.delete()
        return redirect('login:manage_achievements')
    return render(request, 'login/delete_achievement.html', {'achievement': ach})


@login_required
def achievements_catalog_view(request):
    all_achievements = Achievement.objects.all()
    earned_ids = set(UserAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True))
    displayed_ids = set(
        DisplayedAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True))
    return render(request, 'login/achievements_catalog.html',
                  {'achievements': all_achievements, 'earned_ids': earned_ids, 'displayed_ids': displayed_ids})


@require_POST
@login_required
def toggle_displayed_achievement(request):
    achievement_id = request.POST.get('achievement_id')
    action = request.POST.get('action')
    try:
        achievement = Achievement.objects.get(id=achievement_id)
        if not UserAchievement.objects.filter(user=request.user, achievement=achievement).exists():
            return JsonResponse({'error': 'No perm'}, status=403)
        if action == 'add':
            DisplayedAchievement.objects.get_or_create(user=request.user, achievement=achievement)
        elif action == 'remove':
            DisplayedAchievement.objects.filter(user=request.user, achievement=achievement).delete()
        return JsonResponse({'success': True})
    except Achievement.DoesNotExist:
        return JsonResponse({'error': '404'}, status=404)


@login_required
def assign_achievement_view(request):
    if request.method == 'POST':
        form = AssignAchievementForm(request.POST, teacher_user=request.user)
        if form.is_valid():
            student = form.cleaned_data['student']
            ach = form.cleaned_data['achievement']
            UserAchievement.objects.get_or_create(user=student.user, achievement=ach)
            messages.success(request, "Выдано")
            return redirect('login:assign_achievement')
    else:
        form = AssignAchievementForm(teacher_user=request.user)
    return render(request, 'login/assign_achievement.html', {'form': form})


def landing_view(request):
    if request.user.is_authenticated:
        return redirect('login:home')
    return render(request, 'login/landing.html')
