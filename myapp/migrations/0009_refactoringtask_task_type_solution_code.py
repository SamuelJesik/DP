from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0008_refactoringtask_language_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='refactoringtask',
            name='task_type',
            field=models.CharField(
                choices=[
                    ('refactoring', 'Refactoring'),
                    ('error_detection', 'Error Detection'),
                    ('test_writing', 'Test Writing'),
                ],
                default='refactoring',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='refactoringtask',
            name='solution_code',
            field=models.TextField(
                blank=True,
                help_text='Correct solution — used only for test_writing tasks to validate student tests.',
                null=True,
            ),
        ),
    ]
