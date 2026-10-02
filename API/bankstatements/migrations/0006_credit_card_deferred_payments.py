# Generated manually for the credit-card deferred-payment integration.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0006_account_credit_card_metadata"),
        ("bankstatements", "0005_multi_product_imports"),
    ]

    operations = [
        migrations.AddField(
            model_name="bankstatementimportbatch",
            name="card_summary",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="bankstatementimportbatch",
            name="deferred_purchases",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.CreateModel(
            name="CreditCardStatementSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("statement_date", models.DateField()),
                ("summary", models.JSONField(default=dict)),
                ("deferred_purchases", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="credit_card_statement_snapshots", to="account.account")),
                ("import_batch", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="credit_card_snapshot", to="bankstatements.bankstatementimportbatch")),
            ],
            options={"ordering": ["-statement_date", "-id"]},
        ),
        migrations.CreateModel(
            name="DeferredPurchase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_key", models.CharField(max_length=180)),
                ("merchant", models.CharField(max_length=255)),
                ("original_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("remaining_balance", models.DecimalField(decimal_places=2, max_digits=14)),
                ("current_installment", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("installment_number", models.PositiveIntegerField(blank=True, null=True)),
                ("installment_count", models.PositiveIntegerField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="deferred_purchases", to="account.account")),
            ],
        ),
        migrations.AddIndex(
            model_name="creditcardstatementsnapshot",
            index=models.Index(fields=["account", "-statement_date"], name="card_snapshot_account_date_idx"),
        ),
        migrations.AddConstraint(
            model_name="deferredpurchase",
            constraint=models.UniqueConstraint(fields=("account", "source_key"), name="unique_deferred_purchase_key"),
        ),
    ]
