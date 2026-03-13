from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models.signals import pre_save
from django.dispatch import receiver

# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────

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

ARTEL_FRAME_MAP = {
    "Artel 1": "Рамка Тьюринга",
    "Artel 2": "Рамка Ломоносова",
    "Artel 3": "Рамка Леонардо",
    "Artel 4": "Рамка Архимеда",
    "Artel 5": "Рамка Ньютона",
}

DEFAULT_FRAME_NAME = "Стандартная рамка"


# ─────────────────────────────────────────
# RBAC: Permission → Role → User
# ─────────────────────────────────────────

class Permission(models.Model):
    codename = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Кодовое имя",
        help_text="Например: can_award_points"
    )
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
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name="Роль")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, verbose_name="Право")

    class Meta:
        unique_together = ('role', 'permission')
        verbose_name = "Право роли"
        verbose_name_plural = "Права ролей"

    def __str__(self):
        return f"{self.role} → {self.permission.codename}"


# ─────────────────────────────────────────
# SHOP
# ─────────────────────────────────────────

class ShopItem(models.Model):
    TYPE_CHOICES = [
        ('cosmetic', 'Косметика (Для всех)'),
        ('merch', 'Мерч (Только для топ рейтинга)'),
        ('frame', 'Рамка для аватара'),
    ]

    name = models.CharField(max_length=100, verbose_name="Название товара")
    description = models.TextField(verbose_name="Описание", blank=True)
    price = models.PositiveIntegerField(verbose_name="Цена (в монетах)")
    image = models.ImageField(upload_to='shop/', verbose_name="Изображение", blank=True, null=True)
    quantity = models.PositiveIntegerField(default=10, verbose_name="Остаток на складе")
    is_available = models.BooleanField(default=True, verbose_name="Доступен для покупки")
    item_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='cosmetic',
        verbose_name="Тип товара"
    )
    allowed_roles = models.ManyToManyField(
        Role,
        blank=True,
        related_name='available_items',
        verbose_name="Доступно ролям",
        help_text="Оставьте пустым — доступно всем"
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары в магазине"

    def __str__(self):
        return f"[{self.get_item_type_display()}] {self.name}"

    def is_accessible_by(self, user_profile: 'UserProfile') -> bool:
        if not self.allowed_roles.exists():
            return True
        return self.allowed_roles.filter(pk__in=user_profile.roles.all()).exists()


# ─────────────────────────────────────────
# GROUP
# ─────────────────────────────────────────

class Group(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название группы (класса)")
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_groups',
        verbose_name="Куратор (педагог)"
    )

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.name


# ─────────────────────────────────────────
# USER PROFILE
# ─────────────────────────────────────────

class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Пользователь"
    )
    roles = models.ManyToManyField(
        Role,
        through='UserRole',
        blank=True,
        related_name='users',
        verbose_name="Роли"
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name="Аватарка")
    active_frame = models.ForeignKey(
        ShopItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_wearing',
        limit_choices_to={'item_type': 'frame'},
        verbose_name="Активная рамка"
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    balance = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Баланс")
    rating_points = models.PositiveIntegerField(default=0, verbose_name="Рейтинговые очки")
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name="Группа (класс)"
    )
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

    # ── RBAC helpers ──────────────────────────────────────────

    def has_role(self, role_name: str) -> bool:
        return self.roles.filter(name=role_name).exists()

    def has_permission(self, codename: str) -> bool:
        return Permission.objects.filter(
            codename=codename,
            roles__users=self
        ).exists()

    def get_all_permissions(self) -> models.QuerySet:
        return Permission.objects.filter(roles__users=self).distinct()

    # ── Business logic ────────────────────────────────────────

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


class UserRole(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="Профиль")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name="Роль")
    granted_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата выдачи")
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_roles',
        verbose_name="Выдал"
    )

    class Meta:
        unique_together = ('profile', 'role')
        verbose_name = "Роль пользователя"
        verbose_name_plural = "Роли пользователей"

    def __str__(self):
        return f"{self.profile} → {self.role}"


# ─────────────────────────────────────────
# ACHIEVEMENTS
# ─────────────────────────────────────────

def achievement_icon_upload_to(instance, filename):
    safe_name = instance.name.replace(" ", "_").replace("/", "_")
    return f'achievements/icons/{safe_name}.png'


class Achievement(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    requirements = models.TextField(verbose_name="Требования для получения")
    icon = models.ImageField(upload_to=achievement_icon_upload_to, verbose_name="Иконка (PNG)")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Создал"
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


# ─────────────────────────────────────────
# PURCHASES
# ─────────────────────────────────────────

class Purchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает выдачи'),
        ('completed', 'Выдано'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases', verbose_name="Покупатель")
    item = models.ForeignKey(ShopItem, on_delete=models.SET_NULL, null=True, verbose_name="Товар")
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата покупки")
    price_at_moment = models.PositiveIntegerField(verbose_name="Цена на момент покупки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")

    class Meta:
        verbose_name = "Покупка"
        verbose_name_plural = "История покупок"
        ordering = ['-purchased_at']

    def __str__(self):
        item_name = self.item.name if self.item else "Удалённый товар"
        return f"{self.user.username} купил {item_name}"


# ─────────────────────────────────────────
# SIGNALS
# ─────────────────────────────────────────

@receiver(pre_save, sender=UserProfile)
def handle_artel_change(sender, instance, **kwargs):
    if not instance.artel:
        return

    if instance.pk:
        try:
            old_profile = UserProfile.objects.get(pk=instance.pk)
            if old_profile.artel == instance.artel:
                return
        except UserProfile.DoesNotExist:
            pass

    target_frame_name = ARTEL_FRAME_MAP.get(instance.artel)
    if not target_frame_name:
        return

    try:
        frame_item, _ = ShopItem.objects.get_or_create(
            name=target_frame_name,
            defaults={
                'item_type': 'frame',
                'price': 0,
                'description': f'Уникальная рамка для {instance.get_artel_display()}',
                'is_available': False,
                'quantity': 999999,
            }
        )
        if instance.pk and instance.user_id:
            Purchase.objects.get_or_create(
                user_id=instance.user_id,
                item=frame_item,
                defaults={'price_at_moment': 0, 'status': 'completed'}
            )
        instance.active_frame = frame_item

    except Exception as e:
        print(f"Ошибка при выдаче рамки артеля: {e}")