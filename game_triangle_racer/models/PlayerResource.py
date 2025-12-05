from django.db import models


class PlayerResource(models.Model):
    """ """

    player = models.ForeignKey('Player', on_delete=models.CASCADE)
    resource = models.ForeignKey('Resource', on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('player', 'resource'), name='unique_player_resource'),
        )

    def __str__(self):

        return self.resource.__str__()
