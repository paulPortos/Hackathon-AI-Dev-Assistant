from django.urls import path

from multi_agent.views import SeniorDevMessageListView, SeniorDevSessionDetailView, SeniorDevSessionListView


app_name = 'multi_agent'

urlpatterns = [
    path('sr-dev/sessions/', SeniorDevSessionListView.as_view(), name='senior-dev-session-list'),
    path('sr-dev/sessions/<int:session_id>/', SeniorDevSessionDetailView.as_view(), name='senior-dev-session-detail'),
    path('sr-dev/sessions/<int:session_id>/messages/', SeniorDevMessageListView.as_view(), name='senior-dev-message-list'),
]
