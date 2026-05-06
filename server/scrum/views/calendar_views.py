from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from dateutil import rrule
from scrum.models import Card, Event
from scrum.serializers.calendar_serializers import (
    CalendarCardSerializer, CalendarEventSerializer, EventSerializer
)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

class CalendarRangeView(APIView):
    def get(self, request, *args, **kwargs):
        start_str = request.query_params.get('start')
        end_str = request.query_params.get('end')
        
        if not start_str or not end_str:
            return Response({"error": "Missing start or end query parameters"}, status=400)
            
        start = parse_datetime(start_str)
        end = parse_datetime(end_str)
        
        if not start or not end:
            return Response({"error": "Invalid date format"}, status=400)

        # Ensure we have timezones
        if timezone.is_naive(start):
            start = timezone.make_aware(start)
        if timezone.is_naive(end):
            end = timezone.make_aware(end)

        # Fetch Cards
        cards = Card.objects.filter(
            start_datetime__range=(start, end)
        ).select_related('column', 'column__board')
        
        # Fetch Events
        events = Event.objects.filter(
            start_datetime__lte=end
        )
        
        card_data = CalendarCardSerializer(cards, many=True).data
        
        # Expand and Filter Events
        expanded_events = []
        for event in events:
            if not event.recurrence_rule:
                # Standalone event - check if it falls in range
                if event.start_datetime >= start:
                    expanded_events.append(CalendarEventSerializer(event).data)
            else:
                # Recurring event - expand via rrule
                try:
                    rule = rrule.rrulestr(event.recurrence_rule, dtstart=event.start_datetime)
                    occurrences = rule.between(start, end, inc=True)
                    
                    duration = None
                    if event.end_datetime:
                        duration = event.end_datetime - event.start_datetime
                    
                    for occ in occurrences:
                        # Convert naive datetime from rrule to aware
                        if timezone.is_naive(occ):
                            occ = timezone.make_aware(occ)
                            
                        evt_copy = CalendarEventSerializer(event).data
                        evt_copy['start'] = occ.isoformat()
                        if duration:
                            evt_copy['end'] = (occ + duration).isoformat()
                        else:
                            evt_copy['end'] = None
                        
                        expanded_events.append(evt_copy)
                except Exception:
                    # Fallback for invalid rrule
                    if event.start_datetime >= start and event.start_datetime <= end:
                        expanded_events.append(CalendarEventSerializer(event).data)

        # Merge and sort
        unified = sorted(
            list(card_data) + expanded_events,
            key=lambda x: x['start']
        )
        
        return Response(unified)
