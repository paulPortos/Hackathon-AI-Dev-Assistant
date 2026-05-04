from django.urls import path

from user_descriptions.views import UserDescriptionDetailView, UserDescriptionListView, UserDescriptionMeView


app_name = 'user_descriptions'

urlpatterns = [
    path('', UserDescriptionListView.as_view(), name='user-description-list'),
    path('me/', UserDescriptionMeView.as_view(), name='user-description-me'),
    path('<int:pk>/', UserDescriptionDetailView.as_view(), name='user-description-detail'),
]
