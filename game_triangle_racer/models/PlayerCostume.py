from django.db import models


class PlayerCostume(models.Model):
    """ """

    player = models.ForeignKey('Player', on_delete=models.CASCADE)
    costume = models.ForeignKey('Costume', on_delete=models.CASCADE)

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('player', 'costume'), name='unique_player_costume'),
        )

    def __str__(self):

        return self.costume.__str__()
