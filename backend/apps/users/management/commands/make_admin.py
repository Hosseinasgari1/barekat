from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Create (or update) the main SUPER ADMIN account that logs in with username + password."

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Admin username, e.g. superadmin')
        parser.add_argument('password', type=str, help='Admin password')
        parser.add_argument('--first-name', type=str, default='مدیر', help='Optional first name')

    def handle(self, *args, **options):
        username = options['username'].strip()
        password = options['password']
        first_name = options['first_name']

        phone_identifier = f'admin:{username}'
        user, created = User.objects.get_or_create(
            admin_username=username,
            defaults={
                'phone_number': phone_identifier,
                'role': User.Roles.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'is_super_admin': True,
                'admin_permissions': ['approve_products'],
                'first_name': first_name,
            },
        )

        # Ensure existing account is a super admin as well
        user.role = User.Roles.ADMIN
        user.is_super_admin = True
        user.is_staff = True
        user.is_active = True
        if not user.admin_permissions:
            user.admin_permissions = ['approve_products']
        user.set_password(password)
        user.save()

        action = 'created' if created else 'updated'
        self.stdout.write(self.style.SUCCESS(
            f"Super admin '{username}' {action}. Log in at /admin/login with this username and password."
        ))
