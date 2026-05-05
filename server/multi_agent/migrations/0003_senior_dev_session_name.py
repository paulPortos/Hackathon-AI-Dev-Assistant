from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('multi_agent', '0002_project_manager_agent_run'),
    ]

    operations = [
        migrations.AddField(
            model_name='seniordevsession',
            name='name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
