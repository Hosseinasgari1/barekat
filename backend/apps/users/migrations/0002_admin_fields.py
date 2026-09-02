from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(max_length=150, primary_key=True, serialize=False, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='admin_username',
            field=models.CharField(blank=True, max_length=150, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_super_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='admin_permissions',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
