from django.db import models
from .. import helpers


class PlayerTimer(models.Model):
    """ """

    class State(models.IntegerChoices):
        PLANNED = (1, 'Planned', )
        WORKING = (2, 'Working', )
        EXPIRED = (3, 'Expired', )

    player = models.ForeignKey('Player', on_delete=models.CASCADE)
    timer = models.ForeignKey('Timer', on_delete=models.CASCADE)
    state = models.PositiveSmallIntegerField(choices=State.choices, default=State.PLANNED)
    start_datetime = models.DateTimeField(default=helpers.datetime_now_utc)
    remaining = models.PositiveIntegerField(default=0)  #@ Function or property?

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('player', 'timer'), name='unique_player_timer'),
        )

    def __str__(self):

        return self.timer.__str__()

    def update(self):

        utcnow = helpers.datetime_now_utc()
        utcrun = self.start_datetime

        if utcnow >= utcrun:
            delta_ms = int((utcnow - utcrun).total_seconds() * 1000.0)
            durat_ms = self.timer.duration

            d = durat_ms - delta_ms
            if d > 0:
                self.state = PlayerTimer.State.WORKING
                self.remaining = d
            else:
                self.state = PlayerTimer.State.EXPIRED
                self.remaining = 0

            self.save()
