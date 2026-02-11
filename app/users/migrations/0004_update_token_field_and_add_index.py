# Generated manually on 2026-02-11
# Fixes for critical security issues and improvements

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_rename_password_re_token_c5e8e9_idx_password_re_token_060a1f_idx_and_more"),
    ]

    operations = [
        # Increase token field size from 64 to 128 characters
        migrations.AlterField(
            model_name="passwordresettoken",
            name="token",
            field=models.CharField(
                db_index=True,
                help_text="Unique token for password reset",
                max_length=128,
                unique=True,
            ),
        ),
        # Add index on expires_at field for faster cleanup queries
        migrations.AddIndex(
            model_name="passwordresettoken",
            index=models.Index(fields=["expires_at"], name="password_re_expires_9a1b2c_idx"),
        ),
    ]
