# login/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

# === Константы ===
ACTIVITY_MAX_POINTS = 100

ACTIVITY_TITLES = {
    'volunteering': 'Волонтёрство',
    'contests': 'Участие в конкурсах',
    'academic': 'Учебная активность',
    'extracurricular': 'Внеучебная активность',
    'projects': 'Проектная деятельность',
}

TITLES_BY_ACTIVITY = {
    'volunteering': 'Волонтёр года',
    'contests': 'Чемпион конкурсов',
    'academic': 'Золотой студент',
    'extracurricular': 'Активист школы',
    'projects': 'Мастер проектов',
}

ARTEL_CHOICES = [
    ("Artel 1", "Артель 1"),
    ("Artel 2", "Артель 2"),
    ("Artel 3", "Артель 3"),
    ("Artel 4", "Артель 4"),
]

class Group(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название группы (класса)")
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_groups',
        limit_choices_to={'profile__role': 'teacher'},
        verbose_name="Куратор (педагог)"
    )

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.name


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
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name="Группа (класс)"
    )
    artel = models.CharField(
        max_length=20,
        choices=ARTEL_CHOICES,
        blank=True,  # ← разрешает пустое значение в формах
        null=True,  # ← разрешает NULL в базе данных
    )
    rank = models.CharField(
        max_length=100,  # увеличено на случай нескольких званий
        blank=True,
        verbose_name="Звание"
    )

    # === Очки по категориям активности ===
    volunteering_points = models.PositiveIntegerField(default=0, verbose_name="Очки: Волонтёрство")
    contests_points = models.PositiveIntegerField(default=0, verbose_name="Очки: Конкурсы")
    academic_points = models.PositiveIntegerField(default=0, verbose_name="Очки: Учебная активность")
    extracurricular_points = models.PositiveIntegerField(default=0, verbose_name="Очки: Внеучебная активность")
    projects_points = models.PositiveIntegerField(default=0, verbose_name="Очки: Проектная деятельность")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    def update_rank_if_needed(self):
        """Обновляет звание: включает только те звания, по которым набрано >=100 очков."""
        if self.role != 'student':
            return

        # Определяем, какие звания заслужены СЕЙЧАС
        achieved_titles = []
        for key, title in TITLES_BY_ACTIVITY.items():
            points = getattr(self, f"{key}_points", 0)
            if points >= ACTIVITY_MAX_POINTS:
                achieved_titles.append(title)

        # Объединяем в строку (или оставляем пустой)
        new_rank = ", ".join(sorted(set(achieved_titles)))

        # Обновляем ТОЛЬКО если изменилось
        if new_rank != self.rank:
            self.rank = new_rank
            self.save(update_fields=['rank'])

def achievement_icon_upload_to(instance, filename):
    # Сохраняем как: achievements/icons/<название>.png
    safe_name = instance.name.replace(" ", "_").replace("/", "_")
    return f'achievements/icons/{safe_name}.png'


class Achievement(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    requirements = models.TextField(verbose_name="Требования для получения")
    icon = models.ImageField(
        upload_to=achievement_icon_upload_to,
        verbose_name="Иконка (PNG)",
        help_text="Только PNG, рекомендуемый размер: 128x128"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'profile__role': 'teacher'},
        verbose_name="Создал педагог"
    )
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
    """Достижения, выбранные учеником для отображения в профиле"""
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