from django.db import models

class Comment(models.Model):
    card = models.ForeignKey('scrum.Card', on_delete=models.CASCADE, related_name='comments')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'kanban_comment'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on {self.card.title} at {self.created_at}"
