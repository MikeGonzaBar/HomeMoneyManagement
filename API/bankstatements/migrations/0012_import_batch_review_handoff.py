from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("bankstatements", "0011_bankstatement_processing_retries"),
    ]

    operations = [
        migrations.AddField(
            model_name="bankstatementimportbatch",
            name="draft_account",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="draft_bank_statement_import_batches", to="account.account"),
        ),
        migrations.AddField(
            model_name="bankstatementimportbatch",
            name="draft_new_account",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="bankstatementimportbatch",
            name="scan_summary",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
