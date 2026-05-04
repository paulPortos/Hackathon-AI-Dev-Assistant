from rest_framework.generics import ListAPIView

from user_descriptions.selectors import user_description_list
from user_descriptions.serializers import UserDescriptionSerializer


class UserDescriptionListView(ListAPIView):
    serializer_class = UserDescriptionSerializer

    def get_queryset(self):
        return user_description_list()
