from django.db import models

class Label(models.Model):
    board = models.ForeignKey('scrum.Board', on_delete=models.CASCADE, related_name='labels')
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=7)  # Hex string like #FFFFFF

    class Meta:
        db_table = 'kanban_label'

    def __str__(self):
        return f"{self.board.name} - {self.name}"
