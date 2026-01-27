from django.db import models


class ConfigOfInitialPlayerResource(models.Model):
    """Конфигурация начального количества ресурсов для новых игроков."""

    resource = models.OneToOneField('Resource', unique=True, on_delete=models.CASCADE)
    initial_count = models.PositiveIntegerField(default=0, help_text="Начальное количество ресурса")

    def __str__(self):
        return f"Начальное '{self.resource.name}' x {self.initial_count}"
