# Generated by Django 5.1.5 on 2025-02-07 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance_data", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="financialdata",
            name="ticker",
            field=models.CharField(max_length=10),
        ),
    ]
