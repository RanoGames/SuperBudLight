# login/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'login'

urlpatterns = [
path('', views.landing_view, name='landing.html'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('home/', views.home_view, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/equip-frame/', views.equip_frame_view, name='equip_frame'), # <--- НОВЫЙ
    path('my-students/', views.teacher_students_view, name='teacher_students'),
    path('student/<int:student_id>/edit/', views.edit_student_view, name='edit_student'),
    path('award-points/', views.award_points_view, name='award_points'),
    path('rating/', views.rating_view, name='rating'),
    path('artel-rating/', views.artel_rating_view, name='artel_rating'),
    path('my-artel-rating/', views.my_artel_rating_view, name='my_artel_rating'),
    path('achievements/manage/', views.manage_achievements_view, name='manage_achievements'),
    path('achievements/manage/edit/<int:achievement_id>/', views.edit_achievement_view, name='edit_achievement'),
    path('achievements/manage/delete/<int:achievement_id>/', views.delete_achievement_view, name='delete_achievement'),
    path('achievements/', views.achievements_catalog_view, name='achievements_catalog'),
    path('achievements/toggle/', views.toggle_displayed_achievement, name='toggle_displayed_achievement'),
    path('achievements/assign/', views.assign_achievement_view, name='assign_achievement'),
    path('shop/', views.shop_view, name='shop'),
    path('shop/buy/<int:item_id>/', views.buy_item_view, name='buy_item'),
]