# management/commands/setup_roles.py
from django.core.management.base import BaseCommand
from login.models import Role, Permission, RolePermission

PERMISSIONS = [
    ('can_award_points',       'Начислять очки студентам'),
    ('can_create_achievement', 'Создавать достижения'),
    ('can_manage_shop',        'Управлять магазином'),
    ('can_view_all_profiles',  'Просматривать все профили'),
    ('can_buy_items',          'Покупать товары в магазине'),
    ('can_manage_groups',      'Управлять группами'),
]

ROLES = {
    'student': {
        'display_name': 'Ученик',
        'permissions': ['can_buy_items'],
    },
    'teacher': {
        'display_name': 'Педагог',
        'permissions': [
            'can_award_points',
            'can_create_achievement',
            'can_view_all_profiles',
            'can_manage_groups',
        ],
    },
    'admin': {
        'display_name': 'Администратор',
        'permissions': [p[0] for p in PERMISSIONS],  # все права
    },
}

class Command(BaseCommand):
    help = 'Создаёт базовые роли и права RBAC'

    def handle(self, *args, **kwargs):
        for codename, name in PERMISSIONS:
            perm, created = Permission.objects.get_or_create(codename=codename, defaults={'name': name})
            self.stdout.write(f"{'✅ Создано' if created else '⏩ Уже есть'}: {perm}")

        for role_name, data in ROLES.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={'display_name': data['display_name']}
            )
            for codename in data['permissions']:
                perm = Permission.objects.get(codename=codename)
                RolePermission.objects.get_or_create(role=role, permission=perm)
            self.stdout.write(f"{'✅ Роль создана' if created else '⏩ Роль есть'}: {role}")

        self.stdout.write(self.style.SUCCESS('\nRBAC настроен успешно!'))

'''Запускается командой: python manage.py setup_roles'''
