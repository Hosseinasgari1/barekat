from django.db import migrations

def create_default_admin(apps, schema_editor):
    User = apps.get_model('users', 'User')
    from django.contrib.auth.hashers import make_password

    username = 'superadmin'
    phone_identifier = f'admin:{username}'

    user = User.objects.filter(admin_username=username).first()
    if not user:
        user = User(
            phone_number=phone_identifier,
            admin_username=username,
            role='ADMIN',
            is_staff=True,
            is_superuser=True,
            is_active=True,
            is_super_admin=True,
            admin_permissions=['approve_products'],
            first_name='مدیر',
        )
    else:
        user.role = 'ADMIN'
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.is_super_admin = True
        if not user.admin_permissions:
            user.admin_permissions = ['approve_products']

    user.password = make_password('admin123')
    user.save()

def reverse_func(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_admin_fields'),
    ]

    operations = [
        migrations.RunPython(create_default_admin, reverse_func),
    ]
