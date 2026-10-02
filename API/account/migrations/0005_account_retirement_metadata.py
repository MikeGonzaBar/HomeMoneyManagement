from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("account", "0004_account_owner_user_decimal_money")]

    operations = [
        migrations.AddField(
            model_name="account",
            name="retirement_metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
