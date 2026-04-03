from django.contrib import admin
from .models import Achievement, UserAchievement, DisplayedAchievement


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at')
    search_fields = ('name',)


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'earned_at')
    list_filter = ('achievement',)


@admin.register(DisplayedAchievement)
class DisplayedAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'display_order')
