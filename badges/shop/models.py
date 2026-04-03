from django.db import models
from django.contrib.auth.models import User


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
        'login.Role',
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

    def is_accessible_by(self, user_profile) -> bool:
        if not self.allowed_roles.exists():
            return True
        return self.allowed_roles.filter(pk__in=user_profile.roles.all()).exists()


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


# Signal: auto-assign artel frame on artel change
ARTEL_FRAME_MAP = {
    "Artel 1": "Рамка Тьюринга",
    "Artel 2": "Рамка Ломоносова",
    "Artel 3": "Рамка Леонардо",
    "Artel 4": "Рамка Архимеда",
    "Artel 5": "Рамка Ньютона",
}


def _connect_artel_signal():
    """Called from ShopConfig.ready() after all apps are loaded."""
    from django.db.models.signals import pre_save
    from profile_app.models import UserProfile
    pre_save.connect(handle_artel_change, sender=UserProfile)


def handle_artel_change(sender, instance, **kwargs):
    if not instance.artel:
        return

    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            if old.artel == instance.artel:
                return
        except sender.DoesNotExist:
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
                'description': f'Уникальная рамка для артели',
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
