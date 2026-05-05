from django.contrib.auth import get_user_model
from django.db.models import Q


def user_search(query):
    user_model = get_user_model()
    normalized_query = (query or '').strip()
    if not normalized_query:
        return user_model.objects.none()

    return user_model.objects.filter(
        Q(username__icontains=normalized_query)
        | Q(email__icontains=normalized_query)
    )
