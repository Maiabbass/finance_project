# Generated by Django 5.1.5 on 2025-02-11 18:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance_data", "0002_alter_financialdata_ticker"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(blank=True, max_length=15, null=True),
                ),
                ("address", models.TextField(blank=True, null=True)),
                ("birth_date", models.DateField(blank=True, null=True)),
                ("nationality", models.CharField(blank=True, max_length=50, null=True)),
                (
                    "balance",
                    models.DecimalField(decimal_places=2, default=0, max_digits=15),
                ),
                ("is_trader", models.BooleanField(default=False)),
                (
                    "profile_picture",
                    models.ImageField(blank=True, null=True, upload_to="profile_pics/"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("otp_code", models.CharField(blank=True, max_length=6, null=True)),
                ("otp_expiry", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
