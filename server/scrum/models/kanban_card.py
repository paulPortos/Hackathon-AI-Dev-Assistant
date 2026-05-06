from django.db import models
from scrum.models.calendar_entry import CalendarEntry

class Card(CalendarEntry):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    column = models.ForeignKey('scrum.Column', on_delete=models.CASCADE, related_name='cards')
    position = models.IntegerField(default=0)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    labels = models.ManyToManyField('scrum.Label', through='scrum.CardLabel', related_name='cards')

    class Meta:
        db_table = 'kanban_card'
        ordering = ['position']

    def __str__(self):
        return self.title

class CardLabel(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    label = models.ForeignKey('scrum.Label', on_delete=models.CASCADE)

    class Meta:
        db_table = 'kanban_card_label'
        unique_together = ('card', 'label')
