from django.db import models


class Timer(models.Model):
    """Player's timer types."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=16, unique=True, default=str)
    duration = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
