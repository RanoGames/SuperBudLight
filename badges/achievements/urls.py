from django.urls import path
from . import views

app_name = 'achievements'

urlpatterns = [
    path('achievements/', views.achievements_catalog_view, name='achievements_catalog'),
    path('achievements/toggle/', views.toggle_displayed_achievement, name='toggle_displayed_achievement'),
    path('achievements/manage/', views.manage_achievements_view, name='manage_achievements'),
    path('achievements/manage/edit/<int:achievement_id>/', views.edit_achievement_view, name='edit_achievement'),
    path('achievements/manage/delete/<int:achievement_id>/', views.delete_achievement_view, name='delete_achievement'),
    path('achievements/assign/', views.assign_achievement_view, name='assign_achievement'),
]
