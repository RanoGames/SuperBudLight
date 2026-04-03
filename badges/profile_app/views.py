from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied

from .models import UserProfile, Group, ACTIVITY_TITLES, ACTIVITY_MAX_POINTS
from .forms import AvatarUploadForm, StudentProfileEditForm, AwardPointsForm
from shop.models import ShopItem, Purchase
from achievements.models import DisplayedAchievement


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
            return redirect('profile_app:profile')
    else:
        avatar_form = AvatarUploadForm(instance=profile)

    context = {
        'user': user,
        'profile': profile,
        'max_points': ACTIVITY_MAX_POINTS,
        'avatar_form': avatar_form,
    }

    if profile.is_teacher():
        context['managed_groups'] = Group.objects.filter(teacher=user)
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

    return redirect('profile_app:profile')


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
            return redirect('profile_app:teacher_students')
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
            return redirect('profile_app:award_points')
    else:
        form = AwardPointsForm(teacher_user=request.user)

    return render(request, 'login/award_points.html', {'form': form})
