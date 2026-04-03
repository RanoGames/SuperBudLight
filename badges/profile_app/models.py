from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

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
    ("Artel 5", "Артель 5"),
]

DEFAULT_FRAME_NAME = "Стандартная рамка"


class Group(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название группы (класса)")
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='managed_groups', verbose_name="Куратор (педагог)"
    )

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    roles = models.ManyToManyField(
        'login.Role',
        through='login.UserRole',
        blank=True,
        related_name='users',
        verbose_name="Роли"
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Аватарка")
    active_frame = models.ForeignKey(
        'shop.ShopItem',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='users_wearing',
        limit_choices_to={'item_type': 'frame'},
        verbose_name="Активная рамка"
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    balance = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Баланс")
    rating_points = models.PositiveIntegerField(default=0, verbose_name="Рейтинговые очки")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="Группа (класс)")
    artel = models.CharField(max_length=20, choices=ARTEL_CHOICES, blank=True, null=True)
    rank = models.CharField(max_length=100, blank=True, verbose_name="Звание")

    volunteering_points = models.PositiveIntegerField(default=0, verbose_name="Очки: Волонтёрство")
    contests_points = models.PositiveIntegerField(default=0, verbose_name="Очки: Конкурсы")
    academic_points = models.PositiveIntegerField(default=0, verbose_name="Очки: Учебная активность")
    extracurricular_points = models.PositiveIntegerField(default=0, verbose_name="Очки: Внеучебная активность")
    projects_points = models.PositiveIntegerField(default=0, verbose_name="Очки: Проектная деятельность")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    def has_role(self, role_name: str) -> bool:
        return self.roles.filter(name=role_name).exists()

    def has_permission(self, codename: str) -> bool:
        from login.models import Permission
        return Permission.objects.filter(codename=codename, roles__users=self).exists()

    def get_all_permissions(self):
        from login.models import Permission
        return Permission.objects.filter(roles__users=self).distinct()

    def is_student(self) -> bool:
        return self.has_role('student')

    def is_teacher(self) -> bool:
        return self.has_role('teacher')

    def update_rank_if_needed(self):
        if not self.is_student():
            return
        achieved_titles = []
        for key, title in TITLES_BY_ACTIVITY.items():
            points = getattr(self, f"{key}_points", 0)
            if points >= ACTIVITY_MAX_POINTS:
                achieved_titles.append(title)
        new_rank = ", ".join(sorted(set(achieved_titles)))
        if new_rank != self.rank:
            self.rank = new_rank
            self.save(update_fields=['rank'])
