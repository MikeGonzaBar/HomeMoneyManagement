from django.db import migrations


def enable_pg_stat_statements(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")


def disable_pg_stat_statements(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute("DROP EXTENSION IF EXISTS pg_stat_statements")


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_user_is_admin"),
    ]

    operations = [
        migrations.RunPython(enable_pg_stat_statements, disable_pg_stat_statements),
    ]
