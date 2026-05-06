from rest_framework import serializers
from django.utils import timezone
from scrum.models import Board, Column, Card, Label, Comment

class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ['id', 'name', 'description', 'created_at', 'creator', 'project']
        read_only_fields = ['creator']

class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ['id', 'board', 'name', 'position']
        read_only_fields = ['board']

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['id', 'board', 'name', 'color']
        read_only_fields = ['board']

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'card', 'body', 'created_at']
        read_only_fields = ['card']

class CardSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField()
    labels = LabelSerializer(many=True, read_only=True)
    label_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Label.objects.all(), 
        source='labels', required=False
    )
    due_date = serializers.DateTimeField(source='start_datetime', required=False, allow_null=True)

    class Meta:
        model = Card
        fields = [
            'id', 'column', 'title', 'description', 'position', 
            'due_date', 'priority', 'created_at', 'updated_at', 
            'is_overdue', 'labels', 'label_ids'
        ]
        read_only_fields = ['column']
        extra_kwargs = {
            'description': {'required': False, 'allow_blank': True, 'allow_null': True}
        }

    def get_is_overdue(self, obj):
        if obj.start_datetime:
            return obj.start_datetime < timezone.now()
        return False

class MoveCardSerializer(serializers.Serializer):
    column_id = serializers.IntegerField()
    position = serializers.IntegerField()

class ReorderColumnSerializer(serializers.Serializer):
    position = serializers.IntegerField()
