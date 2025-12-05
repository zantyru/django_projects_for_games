from django.db import models


class Resource(models.Model):
    """Player's resource types."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=16, unique=True, default=str)

    def __str__(self):
        return self.name
