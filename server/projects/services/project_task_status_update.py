def project_task_status_update(*, project_task, status):
    project_task.status = status
    project_task.save(update_fields=['status', 'updated_at'])
    return project_task
