from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0004_account_owner_user_decimal_money"),
        ("bankstatements", "0002_bankstatement_owner_user"),
        ("transaction", "0004_transaction_owner_account_fks_decimal_money"),
        ("users", "0002_authtoken"),
    ]

    operations = [
        migrations.CreateModel(
            name="BankStatementImportBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("detected_account_name", models.CharField(blank=True, max_length=255, null=True)),
                ("detected_account_type", models.CharField(blank=True, max_length=60, null=True)),
                ("initial_balance", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("statement_period_start", models.DateField(blank=True, null=True)),
                ("statement_period_end", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("review", "Review"), ("committed", "Committed")], default="review", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("bank_statement", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="import_batches", to="bankstatements.bankstatement")),
                ("owner_user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bank_statement_import_batches", to="users.user")),
            ],
        ),
        migrations.CreateModel(
            name="BankStatementTransactionCandidate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("transaction_type", models.CharField(max_length=30)),
                ("category", models.CharField(max_length=60)),
                ("date", models.DateField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("possible_matches", models.JSONField(blank=True, default=list)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("imported", "Imported"), ("skipped", "Skipped"), ("linked", "Linked")], default="pending", max_length=20)),
                ("error_message", models.TextField(blank=True, null=True)),
                ("raw_data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("account_fk", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="bank_statement_candidates", to="account.account")),
                ("from_account_fk", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="outgoing_bank_statement_candidates", to="account.account")),
                ("import_batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="candidates", to="bankstatements.bankstatementimportbatch")),
                ("imported_transaction", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="imported_bank_statement_candidates", to="transaction.transaction")),
                ("linked_transaction", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="linked_bank_statement_candidates", to="transaction.transaction")),
                ("owner_user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bank_statement_candidates", to="users.user")),
                ("to_account_fk", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="incoming_bank_statement_candidates", to="account.account")),
            ],
        ),
        migrations.AddIndex(
            model_name="bankstatementimportbatch",
            index=models.Index(fields=["owner_user", "status", "-created_at"], name="bankstatem_owner_u_6d8358_idx"),
        ),
        migrations.AddIndex(
            model_name="bankstatementimportbatch",
            index=models.Index(fields=["bank_statement", "status"], name="bankstatem_bank_st_b51032_idx"),
        ),
        migrations.AddIndex(
            model_name="bankstatementtransactioncandidate",
            index=models.Index(fields=["owner_user", "status", "date"], name="bankstatem_owner_u_f3d094_idx"),
        ),
        migrations.AddIndex(
            model_name="bankstatementtransactioncandidate",
            index=models.Index(fields=["import_batch", "status"], name="bankstatem_import_13f46e_idx"),
        ),
    ]
