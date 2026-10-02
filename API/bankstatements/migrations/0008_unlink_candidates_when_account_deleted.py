from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("bankstatements", "0007_cascade_product_candidates"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bankstatementtransactioncandidate",
            name="account_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bank_statement_candidates",
                to="account.account",
            ),
        ),
        migrations.AlterField(
            model_name="bankstatementtransactioncandidate",
            name="from_account_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="outgoing_bank_statement_candidates",
                to="account.account",
            ),
        ),
        migrations.AlterField(
            model_name="bankstatementtransactioncandidate",
            name="to_account_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="incoming_bank_statement_candidates",
                to="account.account",
            ),
        ),
    ]
