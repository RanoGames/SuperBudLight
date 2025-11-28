# login/urls.py
from django.urls import path
from . import views

app_name = 'login'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('home/', views.home_view, name='home'),
    path('profile/', views.profile_view, name='profile'),  # ← новая строка
    path('my-students/', views.teacher_students_view, name='teacher_students'),
    path('student/<int:student_id>/edit/', views.edit_student_view, name='edit_student'),
    path('award-points/', views.award_points_view, name='award_points'),
    path('rating/', views.rating_view, name='rating'),
    path('artel-rating/', views.artel_rating_view, name='artel_rating'),
]
