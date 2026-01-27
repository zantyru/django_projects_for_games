from django.db import models
from .. import helpers


class PlayerTimer(models.Model):
    """Таймер игрока для отслеживания кулдаунов и восстановления ресурсов."""

    class State(models.IntegerChoices):
        PLANNED = (1, 'Запланирован')
        WORKING = (2, 'Работает')
        EXPIRED = (3, 'Истёк')

    player = models.ForeignKey('Player', on_delete=models.CASCADE)
    timer = models.ForeignKey('Timer', on_delete=models.CASCADE)
    state = models.PositiveSmallIntegerField(choices=State.choices, default=State.PLANNED)
    start_datetime = models.DateTimeField(default=helpers.datetime_now_utc)
    remaining = models.PositiveIntegerField(
        default=0,
        help_text="Оставшееся время в миллисекундах (обновляется при вызове update())"
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('player', 'timer'), name='unique_player_timer'),
        )
        indexes = [
            models.Index(fields=['player', 'timer'], name='player_timer_idx'),
            models.Index(fields=['state'], name='player_timer_state_idx'),
        ]

    def __str__(self):
        return f"{self.player.game_id} - {self.timer.name} ({self.get_state_display()})"

    def update(self):
        """Обновляет состояние таймера на основе текущего времени."""
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

            self.save(update_fields=['state', 'remaining'])
