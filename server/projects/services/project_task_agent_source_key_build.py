import hashlib
import json


def project_task_agent_source_key_build(*, project, handoff_id='', task_data=None):
    task_data = task_data or {}
    source_item_id = str(task_data.get('source_item_id') or '').strip()
    handoff_id = str(handoff_id or '').strip()

    if handoff_id and source_item_id:
        key_payload = {
            'handoff_id': handoff_id,
            'project_id': project.id,
            'source_item_id': source_item_id,
        }
    else:
        key_payload = {
            'handoff_id': handoff_id,
            'project_id': project.id,
            'title': str(task_data.get('title') or '').strip().lower(),
            'category': str(task_data.get('category') or '').strip().lower(),
            'description': str(task_data.get('description') or '').strip().lower(),
            'evidence': task_data.get('evidence') or [],
        }

    encoded_payload = json.dumps(key_payload, sort_keys=True, separators=(',', ':'), default=str)
    return hashlib.sha256(encoded_payload.encode()).hexdigest()
