from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bankstatements", "0012_import_batch_review_handoff"),
    ]

    operations = [
        migrations.AddField(
            model_name="bankstatementtransactioncandidate",
            name="from_uses_batch_draft",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="bankstatementtransactioncandidate",
            name="to_uses_batch_draft",
            field=models.BooleanField(default=False),
        ),
    ]
