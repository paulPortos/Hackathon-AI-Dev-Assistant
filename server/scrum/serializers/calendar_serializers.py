from rest_framework import serializers
from scrum.models import Card, Event

class CalendarCardSerializer(serializers.ModelSerializer):
    source = serializers.CharField(default='card', read_only=True)
    start = serializers.DateTimeField(source='start_datetime')
    end = serializers.DateTimeField(source='end_datetime')
    board = serializers.CharField(source='column.board.name', read_only=True)
    column_name = serializers.CharField(source='column.name', read_only=True)

    class Meta:
        model = Card
        fields = [
            'id', 'source', 'title', 'start', 'end', 
            'all_day', 'color', 'priority', 'column_name', 'board'
        ]

class CalendarEventSerializer(serializers.ModelSerializer):
    source = serializers.CharField(default='event', read_only=True)
    start = serializers.DateTimeField(source='start_datetime')
    end = serializers.DateTimeField(source='end_datetime', required=False, allow_null=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'source', 'title', 'start', 'end', 
            'all_day', 'color', 'recurrence_rule', 'location', 'linked_card'
        ]

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'start_datetime', 'end_datetime',
            'all_day', 'color', 'recurrence_rule', 'is_standalone', 'location', 'linked_card'
        ]

