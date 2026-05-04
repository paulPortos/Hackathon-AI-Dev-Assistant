from django.urls import path

from user_descriptions.views import (
    UserDescriptionDetailView,
    UserDescriptionForUserView,
    UserDescriptionListView,
    UserDescriptionMeView,
)


app_name = 'user_descriptions'

urlpatterns = [
    path('', UserDescriptionListView.as_view(), name='user-description-list'),
    path('current-user/', UserDescriptionMeView.as_view(), name='current-user-description-detail'),
    path('users/<int:user_id>/', UserDescriptionForUserView.as_view(), name='user-description-for-user'),
    path('<int:pk>/', UserDescriptionDetailView.as_view(), name='user-description-detail'),
]
