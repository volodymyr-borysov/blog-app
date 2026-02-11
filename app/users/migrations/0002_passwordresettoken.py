# Generated migration for PasswordResetToken model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, help_text='Unique token for password reset', max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When the token was created')),
                ('expires_at', models.DateTimeField(help_text='When the token expires')),
                ('used_at', models.DateTimeField(blank=True, help_text='When the token was used', null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether the token is still active')),
                ('user', models.ForeignKey(help_text='User requesting password reset', on_delete=django.db.models.deletion.CASCADE, related_name='password_reset_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Password Reset Token',
                'verbose_name_plural': 'Password Reset Tokens',
                'db_table': 'password_reset_tokens',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='passwordresettoken',
            index=models.Index(fields=['token'], name='password_re_token_c5e8e9_idx'),
        ),
        migrations.AddIndex(
            model_name='passwordresettoken',
            index=models.Index(fields=['user', 'is_active'], name='password_re_user_id_e8f9a0_idx'),
        ),
    ]
