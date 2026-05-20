from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion


def backfill_relations(apps, schema_editor):
    Account = apps.get_model("account", "Account")
    Transaction = apps.get_model("transaction", "Transaction")
    User = apps.get_model("users", "User")

    users_by_username = {user.username: user for user in User.objects.all()}
    users_by_id = {str(user.id): user for user in User.objects.all()}
    accounts_by_id = {str(account.id): account for account in Account.objects.all()}

    for item in Transaction.objects.all():
        user = users_by_username.get(item.owner_id) or users_by_id.get(str(item.owner_id))
        update_fields = []

        if user:
            item.owner_user_id = user.id
            item.owner_id = user.username
            update_fields.extend(["owner_user", "owner_id"])

        account = accounts_by_id.get(str(item.account_id)) if item.account_id else None
        if account:
            item.account_fk_id = account.id
            update_fields.append("account_fk")

        from_account = accounts_by_id.get(str(item.from_account_id)) if item.from_account_id else None
        if from_account:
            item.from_account_fk_id = from_account.id
            update_fields.append("from_account_fk")

        to_account = accounts_by_id.get(str(item.to_account_id)) if item.to_account_id else None
        if to_account:
            item.to_account_fk_id = to_account.id
            update_fields.append("to_account_fk")

        if update_fields:
            item.save(update_fields=update_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_authtoken"),
        ("account", "0004_account_owner_user_decimal_money"),
        ("transaction", "0003_alter_transaction_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="owner_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="transactions",
                to="users.user",
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="account_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transactions",
                to="account.account",
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="from_account_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="outgoing_transfers",
                to="account.account",
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="to_account_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="incoming_transfers",
                to="account.account",
            ),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="total",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=14),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="owner_id",
            field=models.CharField(max_length=150),
        ),
        migrations.RunPython(backfill_relations, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["owner_user", "date"], name="transactio_owner__2798ec_idx"),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["owner_id", "date"], name="transactio_owner__3934db_idx"),
        ),
    ]
