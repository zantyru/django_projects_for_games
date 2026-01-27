from django.db import models


class Resource(models.Model):
    """Типы ресурсов игрока (монеты, жизни, звёзды и т.п.)."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=16, unique=True)

    def __str__(self):
        return self.name
