from rest_framework.generics import ListAPIView

from projects.selectors import project_list_for_user
from projects.serializers import ProjectSerializer


class ProjectListView(ListAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return project_list_for_user(self.request.user)
