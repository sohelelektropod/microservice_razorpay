# Generated by Django 4.2.7 on 2024-01-01 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payment_system", "0004_alter_transaction_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
