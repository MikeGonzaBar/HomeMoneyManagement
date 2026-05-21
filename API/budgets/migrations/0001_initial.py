from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("users", "0002_authtoken"),
    ]

    operations = [
        migrations.CreateModel(
            name="Budget",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("month", models.DateField(help_text="First day of the budget month")),
                ("scope", models.CharField(choices=[("overall", "Overall"), ("category", "Category")], max_length=20)),
                ("category", models.CharField(blank=True, max_length=60, null=True)),
                ("limit_amount", models.DecimalField(decimal_places=2, max_digits=14)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner_user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="budgets", to="users.user"),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="budget",
            index=models.Index(fields=["owner_user", "month"], name="budgets_bud_owner_u_bba93b_idx"),
        ),
        migrations.AddIndex(
            model_name="budget",
            index=models.Index(fields=["owner_user", "scope", "category"], name="budgets_bud_owner_u_6a7772_idx"),
        ),
        migrations.AddConstraint(
            model_name="budget",
            constraint=models.UniqueConstraint(
                fields=("owner_user", "month", "scope", "category"),
                name="unique_user_month_scope_category_budget",
            ),
        ),
    ]
