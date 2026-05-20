from django.db import migrations, models
import django.db.models.deletion


def backfill_owner_user(apps, schema_editor):
    BankStatement = apps.get_model("bankstatements", "BankStatement")
    User = apps.get_model("users", "User")
    users_by_username = {user.username: user for user in User.objects.all()}

    for statement in BankStatement.objects.all():
        user = users_by_username.get(statement.user_id)
        if user:
            statement.owner_user_id = user.id
            statement.save(update_fields=["owner_user"])


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_authtoken"),
        ("bankstatements", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="bankstatement",
            name="owner_user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="bank_statements",
                to="users.user",
            ),
        ),
        migrations.RunPython(backfill_owner_user, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name="bankstatement",
            index=models.Index(fields=["owner_user", "-upload_date"], name="bankstatem_owner__6ecb53_idx"),
        ),
        migrations.AddIndex(
            model_name="bankstatement",
            index=models.Index(fields=["user_id", "-upload_date"], name="bankstatem_user_id_f7c4f8_idx"),
        ),
    ]
