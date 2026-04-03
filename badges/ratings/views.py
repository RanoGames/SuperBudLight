from django.db.models import Sum
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from profile_app.models import UserProfile, ARTEL_CHOICES


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
