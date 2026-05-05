from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0004_project_task_agent_metadata'),
    ]

    operations = [
        migrations.CreateModel(
            name='SeniorDevSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('commit_sha', models.CharField(max_length=255)),
                ('branch_name', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(choices=[('active', 'Active'), ('closed', 'Closed')], default='active', max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='senior_dev_sessions', to='projects.project')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='senior_dev_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at', '-created_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='SeniorDevMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('user', 'User'), ('assistant', 'Assistant'), ('tool', 'Tool')], max_length=32)),
                ('input_type', models.CharField(choices=[('text', 'Text'), ('choice', 'Choice'), ('open_text', 'Open text'), ('audio', 'Audio'), ('system', 'System')], default='text', max_length=32)),
                ('text_content', models.TextField(blank=True)),
                ('structured_payload', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='multi_agent.seniordevsession')),
            ],
            options={
                'ordering': ['created_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='SeniorDevClaim',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('category', models.CharField(blank=True, max_length=100)),
                ('status', models.CharField(choices=[('unverified', 'Unverified'), ('verified', 'Verified'), ('refuted', 'Refuted'), ('needs_followup', 'Needs follow-up')], default='unverified', max_length=32)),
                ('evidence', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='claims', to='multi_agent.seniordevmessage')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='claims', to='multi_agent.seniordevsession')),
            ],
            options={
                'ordering': ['-created_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='SeniorDevFinding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('finding_type', models.CharField(choices=[('vulnerability', 'Vulnerability'), ('gap', 'Gap'), ('scalability', 'Scalability'), ('question', 'Question'), ('other', 'Other')], default='other', max_length=32)),
                ('title', models.CharField(max_length=255)),
                ('category', models.CharField(blank=True, max_length=100)),
                ('severity', models.CharField(choices=[('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low'), ('info', 'Info')], default='medium', max_length=32)),
                ('confidence_score', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('confidence_reason', models.TextField(blank=True)),
                ('evidence', models.JSONField(blank=True, default=list)),
                ('status', models.CharField(choices=[('open', 'Open'), ('dismissed', 'Dismissed'), ('handed_off', 'Handed off')], default='open', max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('claim', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='findings', to='multi_agent.seniordevclaim')),
                ('message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='findings', to='multi_agent.seniordevmessage')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='findings', to='multi_agent.seniordevsession')),
            ],
            options={
                'ordering': ['-created_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='SeniorDevToolCall',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tool_name', models.CharField(max_length=100)),
                ('safe_input_summary', models.JSONField(blank=True, default=dict)),
                ('safe_result_summary', models.JSONField(blank=True, default=dict)),
                ('status', models.CharField(choices=[('success', 'Success'), ('error', 'Error')], max_length=32)),
                ('duration_ms', models.PositiveIntegerField(default=0)),
                ('error_code', models.CharField(blank=True, max_length=100)),
                ('commit_sha', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tool_calls', to='multi_agent.seniordevmessage')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tool_calls', to='multi_agent.seniordevsession')),
            ],
            options={
                'ordering': ['created_at', 'id'],
            },
        ),
        migrations.AddIndex(
            model_name='seniordevsession',
            index=models.Index(fields=['user', 'status'], name='multi_agent_user_id_16489a_idx'),
        ),
        migrations.AddIndex(
            model_name='seniordevsession',
            index=models.Index(fields=['project', 'commit_sha'], name='multi_agent_project_b5bcb1_idx'),
        ),
        migrations.AddIndex(
            model_name='seniordevmessage',
            index=models.Index(fields=['session', 'created_at'], name='multi_agent_session_180039_idx'),
        ),
        migrations.AddIndex(
            model_name='seniordevmessage',
            index=models.Index(fields=['session', 'role'], name='multi_agent_session_f644dd_idx'),
        ),
        migrations.AddConstraint(
            model_name='seniordevfinding',
            constraint=models.CheckConstraint(
                check=Q(('confidence_score__isnull', True)) | (Q(('confidence_score__gte', 0)) & Q(('confidence_score__lte', 100))),
                name='senior_dev_finding_confidence_score_0_100',
            ),
        ),
        migrations.AddIndex(
            model_name='seniordevtoolcall',
            index=models.Index(fields=['session', 'tool_name'], name='multi_agent_session_6c60fb_idx'),
        ),
        migrations.AddIndex(
            model_name='seniordevtoolcall',
            index=models.Index(fields=['session', 'status'], name='multi_agent_session_e8fdce_idx'),
        ),
    ]
