from django.db import models

class CalendarEntry(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_datetime = models.DateTimeField(db_index=True, null=True, blank=True)
    end_datetime = models.DateTimeField(db_index=True, null=True, blank=True)
    all_day = models.BooleanField(default=False)
    color = models.CharField(max_length=7, blank=True)  # hex color code
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title
