from django.db import transaction
from rest_framework import viewsets, generics, status, response, permissions
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from scrum.models import Board, Column, Card, Label, Comment
from scrum.serializers.kanban_serializers import (
    BoardSerializer, ColumnSerializer, CardSerializer, 
    LabelSerializer, CommentSerializer, MoveCardSerializer, 
    ReorderColumnSerializer
)
from scrum.filters import CardFilter

class BoardViewSet(viewsets.ModelViewSet):
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project']

    def get_queryset(self):
        return Board.objects.filter(creator=self.request.user)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

class BoardColumnsView(generics.ListCreateAPIView):
    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Column.objects.filter(
            board_id=self.kwargs['id'],
            board__creator=self.request.user
        )

    def perform_create(self, serializer):
        # Verify ownership
        Board.objects.get(id=self.kwargs['id'], creator=self.request.user)
        serializer.save(board_id=self.kwargs['id'])

class ColumnDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ColumnSerializer
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Column.objects.filter(board__creator=self.request.user)

class ColumnReorderView(generics.UpdateAPIView):
    serializer_class = ReorderColumnSerializer
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Column.objects.filter(board__creator=self.request.user)

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        column = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_position = serializer.validated_data['position']
        column.position = new_position
        column.save()
        return response.Response(ColumnSerializer(column).data)

class ColumnCardsView(generics.ListCreateAPIView):
    serializer_class = CardSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = CardFilter
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Card.objects.filter(
            column_id=self.kwargs['id'],
            column__board__creator=self.request.user
        ).prefetch_related('labels')

    def perform_create(self, serializer):
        # Verify ownership
        Column.objects.get(id=self.kwargs['id'], board__creator=self.request.user)
        serializer.save(column_id=self.kwargs['id'])

class CardDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CardSerializer
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Card.objects.filter(column__board__creator=self.request.user).prefetch_related('labels')

class CardMoveView(generics.UpdateAPIView):
    serializer_class = MoveCardSerializer
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Card.objects.filter(column__board__creator=self.request.user)

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        card = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verify target column ownership
        new_column_id = serializer.validated_data['column_id']
        Column.objects.get(id=new_column_id, board__creator=self.request.user)
        
        card.column_id = new_column_id
        card.position = serializer.validated_data['position']
        card.save()
        
        return response.Response(CardSerializer(card).data)

class BoardLabelsView(generics.ListCreateAPIView):
    serializer_class = LabelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Label.objects.filter(
            board_id=self.kwargs['id'],
            board__creator=self.request.user
        )

    def perform_create(self, serializer):
        # Verify ownership
        Board.objects.get(id=self.kwargs['id'], creator=self.request.user)
        serializer.save(board_id=self.kwargs['id'])

class CardLabelsView(generics.GenericAPIView):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        return Card.objects.filter(column__board__creator=self.request.user)

    def post(self, request, *args, **kwargs):
        card = self.get_object()
        label_id = request.data.get('label_id')
        if not label_id:
            return response.Response({"error": "label_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify label ownership
        Label.objects.get(id=label_id, board__creator=self.request.user)
        
        card.labels.add(label_id)
        return response.Response(self.get_serializer(card).data)

    def delete(self, request, *args, **kwargs):
        card = self.get_object()
        label_id = request.data.get('label_id')
        if not label_id:
            return response.Response({"error": "label_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        card.labels.remove(label_id)
        return response.Response(self.get_serializer(card).data)

class CardCommentsView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(
            card_id=self.kwargs['id'],
            card__column__board__creator=self.request.user
        ).order_by('created_at')

    def perform_create(self, serializer):
        # Verify ownership
        Card.objects.get(id=self.kwargs['id'], column__board__creator=self.request.user)
        serializer.save(card_id=self.kwargs['id'])

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    lookup_field = 'id'
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(card__column__board__creator=self.request.user)
