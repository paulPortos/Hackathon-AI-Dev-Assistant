from rest_framework.generics import RetrieveAPIView

from user_descriptions.selectors import user_description_list
from user_descriptions.serializers import UserDescriptionSerializer


class UserDescriptionDetailView(RetrieveAPIView):
    serializer_class = UserDescriptionSerializer

    def get_queryset(self):
        return user_description_list()
