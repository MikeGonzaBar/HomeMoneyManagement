from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("users", "0003_user_theme_preference"),
    ]

    operations = [
        migrations.CreateModel(
            name="Alert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("alert_type", models.CharField(max_length=60)),
                ("severity", models.CharField(choices=[("info", "Info"), ("warning", "Warning"), ("critical", "Critical")], default="info", max_length=20)),
                ("title", models.CharField(max_length=160)),
                ("message", models.TextField()),
                ("object_key", models.CharField(max_length=255)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("dismissed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner_user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="alerts", to="users.user")),
            ],
        ),
        migrations.AddIndex(
            model_name="alert",
            index=models.Index(fields=["owner_user", "dismissed_at", "-created_at"], name="alerts_aler_owner_u_c8d416_idx"),
        ),
        migrations.AddIndex(
            model_name="alert",
            index=models.Index(fields=["owner_user", "alert_type", "object_key"], name="alerts_aler_owner_u_809a76_idx"),
        ),
        migrations.AddConstraint(
            model_name="alert",
            constraint=models.UniqueConstraint(fields=("owner_user", "object_key"), name="unique_active_alert_object_key"),
        ),
    ]
