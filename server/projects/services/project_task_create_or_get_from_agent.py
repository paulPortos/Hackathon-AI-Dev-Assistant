from django.db import IntegrityError, transaction

from projects.models import ProjectTask
from projects.services.project_task_agent_source_key_build import project_task_agent_source_key_build
from projects.services.project_task_confidence_normalize import project_task_confidence_normalize
from projects.services.project_task_create import project_task_create
from projects.services.project_task_evidence_normalize import project_task_evidence_normalize


def project_task_create_or_get_from_agent(*, project, data, handoff_id='', actor_user=None, actor_agent='PM Agent'):
    create_data = dict(data)
    create_data['confidence_score'] = project_task_confidence_normalize(
        create_data.get('confidence_score', create_data.pop('confidence', None))
    )
    create_data['confidence_reason'] = str(create_data.get('confidence_reason') or '').strip()
    create_data['evidence'] = project_task_evidence_normalize(create_data.get('evidence'))
    create_data['agent_source_key'] = project_task_agent_source_key_build(
        project=project,
        handoff_id=handoff_id,
        task_data=create_data,
    )
    create_data['created_by_agent'] = create_data.get('created_by_agent') or actor_agent

    existing_task = ProjectTask.objects.filter(project=project, agent_source_key=create_data['agent_source_key']).first()
    if existing_task:
        return existing_task, False

    try:
        with transaction.atomic():
            return project_task_create(project=project, data=create_data, actor_user=actor_user, actor_agent=actor_agent), True
    except IntegrityError:
        return ProjectTask.objects.get(project=project, agent_source_key=create_data['agent_source_key']), False
