from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthToken",
            fields=[
                ("key", models.CharField(max_length=64, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="auth_tokens",
                        to="users.user",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="authtoken",
            index=models.Index(fields=["user", "revoked_at"], name="users_autht_user_id_7e0a7e_idx"),
        ),
        migrations.AddIndex(
            model_name="authtoken",
            index=models.Index(fields=["revoked_at"], name="users_autht_revoked_d46eb4_idx"),
        ),
    ]
