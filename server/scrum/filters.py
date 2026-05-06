from django_filters import rest_framework as filters
from scrum.models import Card

class CardFilter(filters.FilterSet):
    due_before = filters.IsoDateTimeFilter(field_name='due_date', lookup_expr='lt')
    priority = filters.CharFilter(field_name='priority')

    class Meta:
        model = Card
        fields = ['priority', 'due_before']
