from django.db import models


class Costume(models.Model):
    """Костюмы игрока, которые можно разблокировать и использовать."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=16, unique=True)
    image_url = models.URLField()

    def __str__(self):
        return self.name
