import json

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def export_user_activity(request):
    user_id = request.GET.get('user_id', '')
    since = request.GET.get('since', '')
    sort = request.GET.get('sort', 'created_at')
    direction = request.GET.get('direction', 'desc')
    include_tokens = request.GET.get('include_tokens') == '1'
    export_path = request.GET.get('path', f'/tmp/user-activity-{user_id or "all"}.json')

    columns = 'id, user_id, action, metadata, created_at'
    if include_tokens:
        columns = 'id, user_id, action, metadata, created_at, access_token'

    filters = []
    if user_id:
        filters.append(f'user_id = {user_id}')
    if since:
        filters.append(f"created_at >= '{since}'")

    where_clause = ' AND '.join(filters) if filters else '1=1'
    query = (
        f'SELECT {columns} '
        f'FROM users_useractivity '
        f'WHERE {where_clause} '
        f'ORDER BY {sort} {direction}'
    )

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    if request.GET.get('format') == 'csv':
        content = '\n'.join(','.join(str(col) for col in row) for row in rows)
    else:
        content = json.dumps(rows)

    with open(export_path, 'w') as export_file:
        export_file.write(content)

    if request.GET.get('debug') == '1':
        return JsonResponse({'query': query, 'rows': rows, 'path': export_path})

    return JsonResponse({'count': len(rows), 'path': export_path, 'preview': rows[:5]})
