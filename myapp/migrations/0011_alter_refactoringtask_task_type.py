from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_seed_catalog_tasks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refactoringtask',
            name='task_type',
            field=models.CharField(
                choices=[
                    ('refactoring', 'Refactoring'),
                    ('error_detection', 'Error Detection'),
                    ('test_writing', 'Test Writing'),
                    ('code_extension', 'Code Extension'),
                ],
                default='refactoring',
                max_length=20,
            ),
        ),
    ]
