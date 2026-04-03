from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .models import Achievement, UserAchievement, DisplayedAchievement
from .forms import AchievementForm, AssignAchievementForm
from profile_app.models import UserProfile


@login_required
def manage_achievements_view(request):
    if request.method == 'POST':
        form = AchievementForm(request.POST, request.FILES)
        if form.is_valid():
            ach = form.save(commit=False)
            ach.created_by = request.user
            ach.save()
            return redirect('achievements:manage_achievements')
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
            return redirect('achievements:manage_achievements')
    else:
        form = AchievementForm(instance=ach)
    return render(request, 'login/edit_achievement.html', {'form': form, 'achievement': ach})


@login_required
def delete_achievement_view(request, achievement_id):
    ach = get_object_or_404(Achievement, id=achievement_id, created_by=request.user)
    if request.method == 'POST':
        ach.delete()
        return redirect('achievements:manage_achievements')
    return render(request, 'login/delete_achievement.html', {'achievement': ach})


@login_required
def achievements_catalog_view(request):
    all_achievements = Achievement.objects.all()
    earned_ids = set(UserAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True))
    displayed_ids = set(DisplayedAchievement.objects.filter(user=request.user).values_list('achievement_id', flat=True))
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
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_teacher():
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Только педагоги могут назначать достижения.")
    if request.method == 'POST':
        form = AssignAchievementForm(request.POST, teacher_user=request.user)
        if form.is_valid():
            student = form.cleaned_data['student']
            ach = form.cleaned_data['achievement']
            UserAchievement.objects.get_or_create(user=student.user, achievement=ach)
            messages.success(request, "Выдано")
            return redirect('achievements:assign_achievement')
    else:
        form = AssignAchievementForm(teacher_user=request.user)
    return render(request, 'login/assign_achievement.html', {'form': form})
