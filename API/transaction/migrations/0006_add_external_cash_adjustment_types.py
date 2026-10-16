from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transaction", "0005_rename_transactio_owner__2798ec_idx_transaction_owner_u_ffed42_idx_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="transaction_type",
            field=models.CharField(
                choices=[
                    ("Income", "Income"),
                    ("Expense", "Expense"),
                    ("Transfer", "Transfer"),
                    ("External Deposit", "External cash adjustment - in"),
                    ("External Withdrawal", "External cash adjustment - out"),
                ],
                max_length=30,
            ),
        ),
    ]
