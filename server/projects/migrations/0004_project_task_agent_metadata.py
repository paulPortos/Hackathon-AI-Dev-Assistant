from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0003_projectauditlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='projecttask',
            name='agent_source_key',
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
        migrations.AddField(
            model_name='projecttask',
            name='confidence_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='projecttask',
            name='confidence_score',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='projecttask',
            name='evidence',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AlterField(
            model_name='projectauditlog',
            name='event_type',
            field=models.CharField(
                choices=[
                    ('task_created', 'Task created'),
                    ('task_assigned', 'Task assigned'),
                    ('task_reassigned', 'Task reassigned'),
                    ('task_updated', 'Task updated'),
                    ('task_priority_changed', 'Task priority changed'),
                    ('task_status_changed', 'Task status changed'),
                    ('task_due_date_changed', 'Task due date changed'),
                    ('task_deleted', 'Task deleted'),
                    ('vulnerability_created', 'Vulnerability created'),
                    ('vulnerability_resolved', 'Vulnerability resolved'),
                ],
                max_length=64,
            ),
        ),
        migrations.AddConstraint(
            model_name='projecttask',
            constraint=models.CheckConstraint(
                check=Q(('confidence_score__isnull', True)) | (Q(('confidence_score__gte', 0)) & Q(('confidence_score__lte', 100))),
                name='project_task_confidence_score_0_100',
            ),
        ),
        migrations.AddConstraint(
            model_name='projecttask',
            constraint=models.UniqueConstraint(
                condition=~Q(('agent_source_key', '')),
                fields=('project', 'agent_source_key'),
                name='unique_project_task_agent_source_key',
            ),
        ),
    ]
