from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("account", "0005_account_retirement_metadata"), ("bankstatements", "0004_retirement_statement_imports")]

    operations = [
        migrations.CreateModel(
            name="BankStatementImportProduct",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_product_id", models.CharField(max_length=120)),
                ("name", models.CharField(max_length=255)),
                ("product_type", models.CharField(max_length=60)),
                ("opening_balance", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("closing_balance", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("reconciliation", models.JSONField(blank=True, default=dict)),
                ("positions", models.JSONField(blank=True, default=list)),
                ("import_batch", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="products", to="bankstatements.bankstatementimportbatch")),
                ("linked_account", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="statement_import_products", to="account.account")),
            ],
        ),
        migrations.CreateModel(
            name="ProductStatementSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("closing_balance", models.DecimalField(decimal_places=2, max_digits=14)),
                ("statement_date", models.DateField()),
                ("positions", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="product_statement_snapshots", to="account.account")),
                ("import_product", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="snapshot", to="bankstatements.bankstatementimportproduct")),
            ],
        ),
        migrations.AddConstraint(model_name="bankstatementimportproduct", constraint=models.UniqueConstraint(fields=("import_batch", "source_product_id"), name="unique_import_product_source")),
        migrations.AddField(model_name="bankstatementtransactioncandidate", name="destination_product", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="incoming_candidates", to="bankstatements.bankstatementimportproduct")),
        migrations.AddField(model_name="bankstatementtransactioncandidate", name="source_product", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="outgoing_candidates", to="bankstatements.bankstatementimportproduct")),
    ]
