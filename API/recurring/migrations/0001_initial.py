from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("account", "0004_account_owner_user_decimal_money"),
        ("transaction", "0004_transaction_owner_account_fks_decimal_money"),
        ("users", "0002_authtoken"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecurringTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("transaction_type", models.CharField(choices=[("Income", "Income"), ("Expense", "Expense"), ("Transfer", "Transfer")], max_length=30)),
                ("category", models.CharField(max_length=60)),
                ("total", models.DecimalField(decimal_places=2, max_digits=14)),
                ("frequency", models.CharField(choices=[("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly"), ("yearly", "Yearly")], max_length=20)),
                ("interval", models.PositiveIntegerField(default=1)),
                ("start_date", models.DateField()),
                ("next_due_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("account_fk", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="recurring_transactions", to="account.account")),
                ("from_account_fk", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="outgoing_recurring_transfers", to="account.account")),
                ("owner_user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recurring_transactions", to="users.user")),
                ("to_account_fk", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="incoming_recurring_transfers", to="account.account")),
            ],
        ),
        migrations.CreateModel(
            name="RecurringOccurrence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("due_date", models.DateField()),
                ("status", models.CharField(choices=[("due", "Due"), ("posted", "Posted"), ("skipped", "Skipped")], default="due", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner_user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recurring_occurrences", to="users.user")),
                ("posted_transaction", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="recurring_occurrences", to="transaction.transaction")),
                ("recurring_transaction", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="occurrences", to="recurring.recurringtransaction")),
            ],
        ),
        migrations.AddIndex(
            model_name="recurringtransaction",
            index=models.Index(fields=["owner_user", "active", "next_due_date"], name="recurring_re_owner__7cd1b4_idx"),
        ),
        migrations.AddIndex(
            model_name="recurringtransaction",
            index=models.Index(fields=["owner_user", "transaction_type"], name="recurring_re_owner__c7c1af_idx"),
        ),
        migrations.AddConstraint(
            model_name="recurringoccurrence",
            constraint=models.UniqueConstraint(fields=("recurring_transaction", "due_date"), name="unique_recurring_occurrence_due_date"),
        ),
        migrations.AddIndex(
            model_name="recurringoccurrence",
            index=models.Index(fields=["owner_user", "status", "due_date"], name="recurring_re_owner__076b6a_idx"),
        ),
    ]
