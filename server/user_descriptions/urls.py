from django.urls import include, path

from user_descriptions.views import UserDescriptionDetailView, UserDescriptionListView, UserDescriptionMeView


api_v1_urlpatterns = [
    path('', UserDescriptionListView.as_view(), name='user-description-list'),
    path('me/', UserDescriptionMeView.as_view(), name='user-description-me'),
    path('<int:pk>/', UserDescriptionDetailView.as_view(), name='user-description-detail'),
]

urlpatterns = [
    path(
        'api/<str:version>/user-descriptions/',
        include((api_v1_urlpatterns, 'user_descriptions'), namespace='user-descriptions-api'),
    ),
]
