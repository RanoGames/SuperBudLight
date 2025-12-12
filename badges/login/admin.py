# login/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Group, ShopItem, Purchase, ShopCategory  # ← Добавлены ShopItem и Purchase

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Профиль"
    fields = (
        'role',
        'birth_date',
        'balance',
        'rating_points',
        'group',
        'artel',
        'rank'
    )

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher')
    list_filter = ('teacher',)
    search_fields = ('name',)

# === НОВЫЙ КОД ДЛЯ МАГАЗИНА ===
@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available') # добавили category
    list_filter = ('category', 'is_available') # добавили фильтр справа
    list_editable = ('price', 'is_available')
    search_fields = ('name',)

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'price_at_moment', 'purchased_at')
    list_filter = ('purchased_at',)
    readonly_fields = ('purchased_at',)

@admin.register(ShopCategory)
class ShopCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)