from django.urls import path, include
from rest_framework.routers import DefaultRouter
from scrum.views import ProjectMeetingSettingsView
from scrum.views.kanban_views import (
    BoardViewSet, BoardColumnsView, ColumnDetailView, 
    ColumnReorderView, ColumnCardsView, CardDetailView, 
    CardMoveView, BoardLabelsView, CardLabelsView, 
    CardCommentsView, CommentDetailView
)

from scrum.views.scrum_session_views import ScrumSessionViewSet

app_name = 'scrum'

router = DefaultRouter()
router.register(r'boards', BoardViewSet, basename='board')
router.register(r'sessions', ScrumSessionViewSet, basename='scrum-session')

urlpatterns = [
    path('', include(router.urls)),
    
    # Columns
    path('boards/<int:id>/columns/', BoardColumnsView.as_view(), name='board-columns'),
    path('columns/<int:id>/', ColumnDetailView.as_view(), name='column-detail'),
    path('columns/<int:id>/reorder/', ColumnReorderView.as_view(), name='column-reorder'),
    
    # Cards
    path('columns/<int:id>/cards/', ColumnCardsView.as_view(), name='column-cards'),
    path('cards/<int:id>/', CardDetailView.as_view(), name='card-detail'),
    path('cards/<int:id>/move/', CardMoveView.as_view(), name='card-move'),
    
    # Labels
    path('boards/<int:id>/labels/', BoardLabelsView.as_view(), name='board-labels'),
    path('cards/<int:id>/labels/', CardLabelsView.as_view(), name='card-labels'),
    
    # Comments
    path('cards/<int:id>/comments/', CardCommentsView.as_view(), name='card-comments'),
    path('comments/<int:id>/', CommentDetailView.as_view(), name='comment-detail'),

    path(
        'projects/<int:project_id>/meeting-settings/',
        ProjectMeetingSettingsView.as_view(),
        name='project-meeting-settings-detail'
    ),
]
