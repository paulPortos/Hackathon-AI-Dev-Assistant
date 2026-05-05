from rest_framework.generics import ListAPIView

from users.selectors import user_search
from users.serializers import PublicUserSerializer


class UserSearchView(ListAPIView):
    serializer_class = PublicUserSerializer

    def get_queryset(self):
        return user_search(self.request.query_params.get('q', ''))
