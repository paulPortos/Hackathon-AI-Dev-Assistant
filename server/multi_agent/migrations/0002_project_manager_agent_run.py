from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('multi_agent', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='seniordevmessage',
            name='source_user_message',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assistant_responses', to='multi_agent.seniordevmessage'),
        ),
        migrations.CreateModel(
            name='ProjectManagerAgentRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('handoff_id', models.CharField(db_index=True, max_length=255)),
                ('status', models.CharField(choices=[('completed', 'Completed'), ('rejected', 'Rejected'), ('failed', 'Failed')], default='completed', max_length=32)),
                ('confidence_threshold', models.PositiveSmallIntegerField(default=75)),
                ('input_payload', models.JSONField(blank=True, default=dict)),
                ('output_payload', models.JSONField(blank=True, default=dict)),
                ('rejected_items', models.JSONField(blank=True, default=list)),
                ('created_vulnerability_ids', models.JSONField(blank=True, default=list)),
                ('created_task_ids', models.JSONField(blank=True, default=list)),
                ('reused_task_ids', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_manager_agent_runs', to='projects.project')),
                ('requested_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_manager_agent_runs', to=settings.AUTH_USER_MODEL)),
                ('source_senior_dev_message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_manager_agent_runs', to='multi_agent.seniordevmessage')),
            ],
            options={
                'ordering': ['-created_at', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='projectmanageragentrun',
            constraint=models.CheckConstraint(
                check=Q(('confidence_threshold__gte', 0)) & Q(('confidence_threshold__lte', 100)),
                name='pm_agent_run_confidence_threshold_0_100',
            ),
        ),
        migrations.AddConstraint(
            model_name='projectmanageragentrun',
            constraint=models.UniqueConstraint(
                condition=~Q(('handoff_id', '')),
                fields=('project', 'handoff_id'),
                name='unique_pm_agent_run_project_handoff',
            ),
        ),
        migrations.AddIndex(
            model_name='projectmanageragentrun',
            index=models.Index(fields=['project', 'status'], name='pm_run_project_status_idx'),
        ),
        migrations.AddIndex(
            model_name='projectmanageragentrun',
            index=models.Index(fields=['source_senior_dev_message'], name='pm_run_source_msg_idx'),
        ),
    ]
