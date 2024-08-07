# Generated by Django 4.1 on 2024-05-17 07:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserDetails",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        primary_key=True,
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "email_secret",
                    models.CharField(blank=True, max_length=16, null=True),
                ),
                (
                    "email_verified_at",
                    models.DateTimeField(blank=True, default=None, null=True),
                ),
                (
                    "last_log_out",
                    models.DateTimeField(blank=True, default=None, null=True),
                ),
                (
                    "password_change_secret",
                    models.CharField(
                        blank=True, default=None, max_length=16, null=True
                    ),
                ),
                (
                    "password_change_requested_at",
                    models.DateTimeField(blank=True, default=None, null=True),
                ),
                (
                    "tokens_issued",
                    models.IntegerField(blank=True, default=0, null=True),
                ),
                ("archived", models.IntegerField(blank=True, default=0, null=True)),
            ],
            options={
                "db_table": "user_details",
            },
        ),
    ]
