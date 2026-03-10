from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    UserProfile, Group, ShopItem, Purchase,
    Role, Permission, RolePermission, UserRole
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Профиль"
    fields = (
        'birth_date',
        'balance',
        'rating_points',
        'group',
        'artel',
        'rank',
        'active_frame',
    )

class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1
    fields = ('role', 'granted_by')
    verbose_name = "Роль"
    verbose_name_plural = "Роли пользователя"

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, UserRoleInline)


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
    filter_horizontal = ('allowed_roles',)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'price_at_moment', 'purchased_at', 'status')
    list_filter = ('purchased_at', 'status')
    readonly_fields = ('purchased_at',)


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name')
    search_fields = ('name',)
    inlines = (RolePermissionInline,)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'name')
    search_fields = ('codename', 'name')


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('profile', 'role', 'granted_at', 'granted_by')
    list_filter = ('role',)
    readonly_fields = ('granted_at',)