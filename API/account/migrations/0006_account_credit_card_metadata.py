# Generated manually for the credit-card statement snapshot integration.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0005_account_retirement_metadata"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="credit_card_metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
