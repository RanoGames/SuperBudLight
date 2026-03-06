from django.core.management.base import BaseCommand
from login.models import UserProfile, ShopItem, Purchase, ARTEL_FRAME_MAP


class Command(BaseCommand):
    help = 'Выдает рамки всем пользователям согласно их артели'

    def handle(self, *args, **options):
        students = UserProfile.objects.filter(role='student').exclude(artel__isnull=True).exclude(artel='')

        count = 0
        for profile in students:
            target_frame_name = ARTEL_FRAME_MAP.get(profile.artel)

            if target_frame_name:
                # 1. Находим или создаем рамку
                frame_item, _ = ShopItem.objects.get_or_create(
                    name=target_frame_name,
                    defaults={
                        'item_type': 'frame',
                        'price': 0,
                        'description': f'Рамка для {profile.get_artel_display()}',
                        'is_available': False
                    }
                )

                # 2. Создаем "покупку" (владение), если нет
                Purchase.objects.get_or_create(
                    user=profile.user,
                    item=frame_item,
                    defaults={'price_at_moment': 0, 'status': 'completed'}
                )

                # 3. Надеваем рамку, если она другая
                if profile.active_frame != frame_item:
                    profile.active_frame = frame_item
                    profile.save()
                    count += 1
                    self.stdout.write(f"Updated: {profile.user.username} -> {target_frame_name}")

        self.stdout.write(self.style.SUCCESS(f'Готово! Обновлено профилей: {count}'))