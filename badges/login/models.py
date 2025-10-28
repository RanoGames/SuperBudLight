# login/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Ученик'),
        ('teacher', 'Педагог'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Пользователь"
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        verbose_name="Роль"
    )

    # Поля ТОЛЬКО для учеников
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата рождения"
    )
    balance = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Баланс"
    )
    rating_points = models.PositiveIntegerField(
        default=0,
        verbose_name="Рейтинговые очки"
    )
    group_name = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Группа (класс)"
    )
    artel = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Артель"
    )
    rank = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Звание"
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"