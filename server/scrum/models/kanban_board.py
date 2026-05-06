from django.conf import settings
from django.db import models

class Board(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kanban_boards')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kanban_board'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
