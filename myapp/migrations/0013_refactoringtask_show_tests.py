from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0012_seed_extended_catalog'),
    ]

    operations = [
        migrations.AddField(
            model_name='refactoringtask',
            name='show_tests',
            field=models.BooleanField(
                default=True,
                help_text='If unchecked, students cannot see the unit tests panel for this task.',
            ),
        ),
    ]
