# login/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Профиль"
    fields = (
        'role',
        'birth_date',
        'balance',
        'rating_points',
        'group_name',
        'artel',
        'rank'
    )

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Отключаем стандартную регистрацию User
admin.site.unregister(User)
# Регистрируем с нашим расширением
admin.site.register(User, UserAdmin)