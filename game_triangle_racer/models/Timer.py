from django.db import models


class Timer(models.Model):
    """Типы таймеров игрока (восстановление жизней, кулдауны и т.п.)."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=16, unique=True)
    duration = models.PositiveIntegerField(default=0, help_text="Длительность в миллисекундах")

    def __str__(self):
        return self.name
