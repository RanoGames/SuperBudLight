from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from .models import (
    UserProfile, Group, ShopItem, Purchase,
    Role, Permission, RolePermission, UserRole
)


class CustomUserChangeForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        required=False,
        widget=admin.widgets.FilteredSelectMultiple('Роли', is_stacked=False),
        label='Роли'
    )

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                profile = self.instance.profile
                self.fields['roles'].initial = profile.roles.all()
            except UserProfile.DoesNotExist:
                pass


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
    show_change_link = True


class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    inlines = (UserProfileInline,)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj is not None:
            fieldsets = list(fieldsets) + [
                ('Роли RBAC', {'fields': ('roles',)})
            ]
        return fieldsets

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # При создании нового юзера роли не задаются на первом шаге
        if not change:
            return

        selected_roles = form.cleaned_data.get('roles', [])

        try:
            profile = obj.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=obj)

        UserRole.objects.filter(profile=profile).exclude(role__in=selected_roles).delete()

        for role in selected_roles:
            UserRole.objects.get_or_create(
                profile=profile,
                role=role,
                defaults={'granted_by': request.user}
            )


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1
    fields = ('role', 'granted_by')
    verbose_name = "Роль"
    verbose_name_plural = "Роли пользователя"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_roles', 'balance', 'rating_points', 'group', 'artel')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    inlines = (UserRoleInline,)
    fields = (
        'user',
        'birth_date',
        'balance',
        'rating_points',
        'group',
        'artel',
        'rank',
        'active_frame',
    )

    def get_roles(self, obj):
        roles = obj.roles.all()
        if not roles:
            return '—'
        return ', '.join(r.display_name for r in roles)
    get_roles.short_description = 'Роли'


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