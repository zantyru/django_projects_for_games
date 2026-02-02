from django.db import models


class PlayerResource(models.Model):
    """Связь игрока с ресурсами и их количеством."""

    player = models.ForeignKey('Player', on_delete=models.CASCADE)
    resource = models.ForeignKey('Resource', on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0, help_text="Количество ресурса у игрока")

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('player', 'resource'), name='unique_player_resource'),
        )

    def __str__(self):
        return f"{self.player.game_id} - {self.resource.name}: {self.count}"
