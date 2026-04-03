from django.contrib import admin
from .models import Role, Permission, RolePermission, UserRole


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
