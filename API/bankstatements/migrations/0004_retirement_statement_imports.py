from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0005_account_retirement_metadata"),
        ("bankstatements", "0003_import_reconciliation"),
    ]

    operations = [
        migrations.AddField(model_name="bankstatementimportbatch", name="statement_kind", field=models.CharField(db_index=True, default="bank", max_length=30)),
        migrations.AddField(model_name="bankstatementimportbatch", name="balance_period_start", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="bankstatementimportbatch", name="balance_period_end", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="bankstatementimportbatch", name="movements_period_start", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="bankstatementimportbatch", name="movements_period_end", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="bankstatementimportbatch", name="retirement_breakdown", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="bankstatementimportbatch", name="reconciliation", field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name="bankstatementimportbatch", name="linked_account", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="retirement_import_batches", to="account.account")),
        migrations.CreateModel(
            name="RetirementStatementSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("statement_date", models.DateField()),
                ("opening_balance", models.DecimalField(decimal_places=2, max_digits=14)),
                ("closing_balance", models.DecimalField(decimal_places=2, max_digits=14)),
                ("breakdown", models.JSONField(default=dict)),
                ("balance_period_start", models.DateField(blank=True, null=True)),
                ("balance_period_end", models.DateField(blank=True, null=True)),
                ("movements_period_start", models.DateField(blank=True, null=True)),
                ("movements_period_end", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="retirement_snapshots", to="account.account")),
                ("import_batch", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="retirement_snapshot", to="bankstatements.bankstatementimportbatch")),
            ],
            options={"ordering": ["-statement_date", "-id"]},
        ),
        migrations.AddIndex(model_name="retirementstatementsnapshot", index=models.Index(fields=["account", "-statement_date"], name="bankstateme_account_dc80e1_idx")),
    ]
