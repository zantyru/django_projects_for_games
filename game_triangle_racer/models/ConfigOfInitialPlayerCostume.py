from django.db import models


class ConfigOfInitialPlayerCostume(models.Model):
    """Конфигурация начальных костюмов для новых игроков."""

    costume = models.OneToOneField('Costume', unique=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"Начальный '{self.costume.name}'"
