# Generated by Django 5.1.5 on 2025-02-13 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance_data", "0003_userprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="reset_token",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
