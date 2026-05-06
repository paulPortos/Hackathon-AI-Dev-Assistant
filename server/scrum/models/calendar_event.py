from django.db import models
from scrum.models.calendar_entry import CalendarEntry

class Event(CalendarEntry):
    recurrence_rule = models.CharField(max_length=255, blank=True)
    is_standalone = models.BooleanField(default=False)
    location = models.CharField(max_length=255, blank=True)
    linked_card = models.OneToOneField(
        'scrum.Card', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='event'
    )

    class Meta:
        db_table = 'calendar_event'
