from django.urls import path
from . import views

app_name = 'profile_app'

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('profile/equip-frame/', views.equip_frame_view, name='equip_frame'),
    path('my-students/', views.teacher_students_view, name='teacher_students'),
    path('student/<int:student_id>/edit/', views.edit_student_view, name='edit_student'),
    path('award-points/', views.award_points_view, name='award_points'),
]
