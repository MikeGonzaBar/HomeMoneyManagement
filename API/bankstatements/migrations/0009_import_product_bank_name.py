from django.db import migrations, models


def backfill_bank_names(apps, schema_editor):
    product_model = apps.get_model("bankstatements", "BankStatementImportProduct")
    for product in product_model.objects.select_related("import_batch").filter(bank_name=""):
        product.bank_name = product.import_batch.detected_account_name or ""
        product.save(update_fields=["bank_name"])
    product_model.objects.filter(
        source_product_id="nu-main",
        name="Cuenta Nu",
        product_type="Débito",
    ).update(product_type="Checking")


class Migration(migrations.Migration):
    dependencies = [
        ("bankstatements", "0008_unlink_candidates_when_account_deleted"),
    ]

    operations = [
        migrations.AddField(
            model_name="bankstatementimportproduct",
            name="bank_name",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.RunPython(backfill_bank_names, migrations.RunPython.noop),
    ]
