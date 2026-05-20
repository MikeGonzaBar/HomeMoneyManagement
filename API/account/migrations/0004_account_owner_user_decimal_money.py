from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


def backfill_owner_user(apps, schema_editor):
    Account = apps.get_model("account", "Account")
    User = apps.get_model("users", "User")
    users_by_username = {user.username: user for user in User.objects.all()}

    for account in Account.objects.all():
        user = users_by_username.get(account.owner)
        if user:
            account.owner_user_id = user.id
            account.save(update_fields=["owner_user"])


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_authtoken"),
        ("account", "0003_alter_account_text_lengths"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="owner_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="accounts",
                to="users.user",
            ),
        ),
        migrations.AlterField(
            model_name="account",
            name="total",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=14),
        ),
        migrations.AlterField(
            model_name="account",
            name="credit_limit",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Credit limit for credit card accounts",
                max_digits=14,
                null=True,
            ),
        ),
        migrations.RunPython(backfill_owner_user, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name="account",
            index=models.Index(fields=["owner_user", "account_name"], name="account_acc_owner__0a182f_idx"),
        ),
        migrations.AddIndex(
            model_name="account",
            index=models.Index(fields=["owner"], name="account_acc_owner_79209f_idx"),
        ),
    ]
