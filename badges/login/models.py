from django.db import models
from django.contrib.auth.models import User


class Permission(models.Model):
    codename = models.CharField(max_length=100, unique=True, verbose_name="Кодовое имя")
    name = models.CharField(max_length=200, verbose_name="Читаемое название")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Право доступа"
        verbose_name_plural = "Права доступа"
        ordering = ['codename']

    def __str__(self):
        return f"{self.name} ({self.codename})"


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название роли")
    display_name = models.CharField(max_length=100, verbose_name="Отображаемое название")
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        blank=True,
        related_name='roles',
        verbose_name="Права"
    )

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return self.display_name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'permission')
        verbose_name = "Право роли"
        verbose_name_plural = "Права ролей"

    def __str__(self):
        return f"{self.role} → {self.permission.codename}"


class UserRole(models.Model):
    profile = models.ForeignKey('profile_app.UserProfile', on_delete=models.CASCADE, verbose_name="Профиль")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name="Роль")
    granted_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата выдачи")
    granted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='granted_roles', verbose_name="Выдал"
    )

    class Meta:
        unique_together = ('profile', 'role')
        verbose_name = "Роль пользователя"
        verbose_name_plural = "Роли пользователей"

    def __str__(self):
        return f"{self.profile} → {self.role}"
