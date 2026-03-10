from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Group, ShopItem, Purchase # ← Добавлены ShopItem и Purchase

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
@admin.register(ShopItem)
class ShopItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'item_type', 'price', 'quantity', 'is_available')
    list_filter = ('item_type', 'is_available')
    list_editable = ('price', 'quantity', 'is_available', 'item_type')
    search_fields = ('name',)

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'price_at_moment', 'purchased_at', 'status')
    list_filter = ('purchased_at', 'status')
    readonly_fields = ('purchased_at',)