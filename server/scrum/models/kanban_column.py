from django.db import models

class Column(models.Model):
    board = models.ForeignKey('scrum.Board', on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=255)
    position = models.IntegerField(default=0)

    class Meta:
        db_table = 'kanban_column'
        ordering = ['position']

    def __str__(self):
        return f"{self.board.name} - {self.name}"
