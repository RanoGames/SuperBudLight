# login/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

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

# --- ShopItem ---
class ShopItem(models.Model):
    TYPE_CHOICES = [
        ('cosmetic', 'Косметика (Для всех)'),
        ('merch', 'Мерч (Только для топ рейтинга)'),
        ('frame', 'Рамка для аватара'),  # <--- НОВЫЙ ТИП
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

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары в магазине"

    def __str__(self):
        return f"[{self.get_item_type_display()}] {self.name}"


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

    # === НОВЫЕ ПОЛЯ ===
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name="Аватарка"
    )
    active_frame = models.ForeignKey(
        ShopItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_wearing',
        limit_choices_to={'item_type': 'frame'},
        verbose_name="Активная рамка"
    )
    # ==================

    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    balance = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Баланс")
    rating_points = models.PositiveIntegerField(default=0, verbose_name="Рейтинговые очки")
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='students',
                              verbose_name="Группа (класс)")
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
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    def update_rank_if_needed(self):
        if self.role != 'student':
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


def achievement_icon_upload_to(instance, filename):
    safe_name = instance.name.replace(" ", "_").replace("/", "_")
    return f'achievements/icons/{safe_name}.png'


class Achievement(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    requirements = models.TextField(verbose_name="Требования для получения")
    icon = models.ImageField(upload_to=achievement_icon_upload_to, verbose_name="Иконка (PNG)")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   limit_choices_to={'profile__role': 'teacher'}, verbose_name="Создал педагог")
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


ARTEL_FRAME_MAP = {
    "Artel 1": "Рамка Тьюринга",
    "Artel 2": "Рамка Ломоносова",
    "Artel 3": "Рамка Леонардо",
    "Artel 4": "Рамка Архимеда",
    "Artel 5": "Рамка Ньютона",
}


@receiver(post_save, sender=UserProfile)
def auto_assign_artel_frame(sender, instance, created, **kwargs):
    """
    Сигнал срабатывает каждый раз при сохранении профиля (создание или редактирование).
    """
    # 1. Проверяем, что пользователь ученик и у него выбрана артель
    if instance.role != 'student' or not instance.artel:
        return

    # 2. Получаем название нужной рамки из словаря
    target_frame_name = ARTEL_FRAME_MAP.get(instance.artel)

    if not target_frame_name:
        return  # Для этой артели рамка не настроена

    try:
        # 3. Ищем товар-рамку в базе данных
        # Используем get_or_create, чтобы рамка создалась сама, если её нет
        frame_item, item_created = ShopItem.objects.get_or_create(
            name=target_frame_name,
            defaults={
                'item_type': 'frame',
                'price': 0,  # Бесплатно, так как выдаем автоматом
                'description': f'Эксклюзивная рамка для {instance.get_artel_display()}',
                'is_available': False  # Нельзя купить в магазине, только получить автоматом
            }
        )

        # 4. Проверяем, надета ли уже эта рамка
        if instance.active_frame != frame_item:
            # 5. Выдаем право владения (Purchase), если его еще нет
            Purchase.objects.get_or_create(
                user=instance.user,
                item=frame_item,
                defaults={
                    'price_at_moment': 0,
                    'status': 'completed'
                }
            )

            # 6. Надеваем рамку
            # Важно: используем update(), чтобы не вызвать рекурсию (бесконечный цикл сохранения)
            UserProfile.objects.filter(pk=instance.pk).update(active_frame=frame_item)

            print(f"Updated frame for {instance.user.username} to {target_frame_name}")

    except Exception as e:
        print(f"Error auto-assigning frame: {e}")


@receiver(post_save, sender=UserProfile)
def auto_assign_artel_frame(sender, instance, created, **kwargs):
    """
    Автоматически выдает и надевает рамку при выборе Артели.
    """
    # Если это не ученик или артель не выбрана — ничего не делаем
    if instance.role != 'student' or not instance.artel:
        return

    # Получаем название нужной рамки
    target_frame_name = ARTEL_FRAME_MAP.get(instance.artel)

    if not target_frame_name:
        return

    try:
        # 1. Ищем или создаем товар-рамку (чтобы не было ошибки, если ты забыл создать в админке)
        frame_item, _ = ShopItem.objects.get_or_create(
            name=target_frame_name,
            defaults={
                'item_type': 'frame',
                'price': 0,  # Бесплатно
                'description': f'Уникальная рамка для {instance.get_artel_display()}',
                'is_available': False,  # Не продается в магазине
                'quantity': 999999
            }
        )

        # 2. Проверяем, надета ли уже эта рамка
        if instance.active_frame != frame_item:
            # 3. Выдаем право владения (Purchase)
            Purchase.objects.get_or_create(
                user=instance.user,
                item=frame_item,
                defaults={
                    'price_at_moment': 0,
                    'status': 'completed'
                }
            )

            # 4. Надеваем рамку (используем update, чтобы не вызвать рекурсию сохранения)
            UserProfile.objects.filter(pk=instance.pk).update(active_frame=frame_item)

    except Exception as e:
        print(f"Ошибка при выдаче рамки артеля: {e}")


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """При регистрации выдаем стандартную рамку"""
    if created:
        # Создаем профиль
        profile = UserProfile.objects.create(user=instance, role='student')
        try:
            # Выдаем стандартную рамку
            default_frame, _ = ShopItem.objects.get_or_create(
                name=DEFAULT_FRAME_NAME,
                defaults={'item_type': 'frame', 'price': 0, 'is_available': False, 'quantity': 999999}
            )
            Purchase.objects.get_or_create(
                user=instance, item=default_frame, defaults={'price_at_moment': 0, 'status': 'completed'}
            )
            # Надеваем её
            profile.active_frame = default_frame
            profile.save(update_fields=['active_frame'])
        except Exception as e:
            print(f"Ошибка при выдаче дефолтной рамки: {e}")


@receiver(pre_save, sender=UserProfile)
def check_artel_change_and_assign_frame(sender, instance, **kwargs):
    """
    Следим за сменой Артеля. Если Артель поменялась -> меняем рамку.
    Если просто нажали "Сохранить" (например, сменили баланс или рамку вручную) -> ничего не делаем.
    """
    if instance.role != 'student' or not instance.artel:
        return

    # Если объект уже существует в базе (это редактирование, а не создание)
    if instance.pk:
        try:
            old_profile = UserProfile.objects.get(pk=instance.pk)
            # Проверяем: изменилась ли артель?
            if old_profile.artel == instance.artel:
                # Артель НЕ менялась. Значит, не трогаем рамку.
                return
        except UserProfile.DoesNotExist:
            pass

    # Если мы здесь, значит Артель изменилась (или была назначена впервые)
    target_frame_name = ARTEL_FRAME_MAP.get(instance.artel)

    if target_frame_name:
        try:
            # 1. Находим рамку
            frame_item, _ = ShopItem.objects.get_or_create(
                name=target_frame_name,
                defaults={'item_type': 'frame', 'price': 0, 'is_available': False, 'quantity': 999999}
            )

            # 2. Выдаем право владения (если его нет)
            # Тут нужен user, но pre_save может быть вызван до того как user привязан полностью,
            # но так как это OneToOne, user должен быть.
            if instance.user:
                Purchase.objects.get_or_create(
                    user=instance.user,
                    item=frame_item,
                    defaults={'price_at_moment': 0, 'status': 'completed'}
                )

            # 3. Принудительно надеваем новую рамку
            instance.active_frame = frame_item

        except Exception as e:
            print(f"Error assigning artel frame: {e}")


@receiver(pre_save, sender=UserProfile)
def handle_artel_change(sender, instance, **kwargs):
    """
    Срабатывает ПЕРЕД сохранением.
    Проверяем: изменилась ли Артель?
    Если ДА -> Меняем рамку на артельную.
    Если НЕТ -> Ничего не трогаем (позволяем носить любую рамку).
    """
    # Работаем только со студентами
    if instance.role != 'student':
        return

    # Если профиль только создается (нет ID), пропускаем (это обработает create_user_profile)
    if not instance.pk:
        return

    try:
        # Получаем старую версию профиля из базы данных
        old_profile = UserProfile.objects.get(pk=instance.pk)

        # Сравниваем старую артель и новую
        if old_profile.artel != instance.artel:
            # АРТЕЛЬ ИЗМЕНИЛАСЬ! Выдаем новую рамку.
            print(f"🔄 Смена артеля у {instance.user.username}: {old_profile.artel} -> {instance.artel}")

            target_frame_name = ARTEL_FRAME_MAP.get(instance.artel)
            if target_frame_name:
                # Находим рамку
                frame_item, _ = ShopItem.objects.get_or_create(
                    name=target_frame_name,
                    defaults={'item_type': 'frame', 'price': 0, 'is_available': False, 'quantity': 999999}
                )

                # Выдаем право владения
                if instance.user:
                    Purchase.objects.get_or_create(
                        user=instance.user,
                        item=frame_item,
                        defaults={'price_at_moment': 0, 'status': 'completed'}
                    )

                # Принудительно надеваем
                instance.active_frame = frame_item

    except UserProfile.DoesNotExist:
        pass