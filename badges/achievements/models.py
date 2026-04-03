from django.db import models
from django.contrib.auth.models import User


def achievement_icon_upload_to(instance, filename):
    safe_name = instance.name.replace(" ", "_").replace("/", "_")
    return f'achievements/icons/{safe_name}.png'


class Achievement(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    requirements = models.TextField(verbose_name="Требования для получения")
    icon = models.ImageField(upload_to=achievement_icon_upload_to, verbose_name="Иконка (PNG)")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Создал")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения"
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='earned_by')
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')
        verbose_name = "Полученное достижение"
        verbose_name_plural = "Полученные достижения"

    def __str__(self):
        return f"{self.user.username} → {self.achievement.name}"


class DisplayedAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='displayed_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    display_order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")

    class Meta:
        verbose_name = "Отображаемое достижение"
        verbose_name_plural = "Отображаемые достижения"
        ordering = ['display_order', 'achievement__name']
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.username} → {self.achievement.name} (в профиле)"
