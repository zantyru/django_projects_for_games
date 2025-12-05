from django.db import models


class Config(models.Model):
    """Common setting for whole game."""

    game_default_life_recovery_interval = models.PositiveSmallIntegerField(default=1800)  # 30 minutes
