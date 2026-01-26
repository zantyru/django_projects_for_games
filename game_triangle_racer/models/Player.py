import os
import base64
from datetime import timedelta
from django.db import models
from .. import helpers


class Player(models.Model):
    """Represents a player data and state in the game."""

    game_id = models.AutoField(primary_key=True)  #TODO Rename to 'id'
    session_quasisecret = models.BigIntegerField(default=0)
    regin_stamp = models.BigIntegerField(default=0)
    login_stamp = models.BigIntegerField(default=0)
    start_stamp = models.BigIntegerField(default=0)
    token = models.CharField(max_length=32, unique=True, default=helpers.default_random_string)  #@TODO Проиндексировать
    token_expiration = models.DateTimeField(default=helpers.datetime_now_utc)
    platform = models.CharField(max_length=16)
    platform_id = models.PositiveIntegerField(default=0)

    level = models.PositiveSmallIntegerField(default=0)

    costumes = models.ManyToManyField('Costume', through='PlayerCostume')
    resources = models.ManyToManyField('Resource', through='PlayerResource')
    timers = models.ManyToManyField('Timer', through='PlayerTimer')

    def __str__(self):

        return str(self.game_id)

    def get_token(self, expires_in=3600):

        utcnow = helpers.datetime_now_utc()
        if self.token and self.token_expiration > utcnow + timedelta(seconds=60):
            return self.token

        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = utcnow + timedelta(seconds=expires_in)
        self.save()

        return self.token

    def revoke_token(self):

        utcnow = helpers.datetime_now_utc()
        self.token_expiration = utcnow - timedelta(seconds=1)

    @staticmethod
    def get_player_by_token(token):

        player = Player.objects.filter(token=token).first()

        if player:
            utcnow = helpers.datetime_now_utc()
            if player.token_expiration < utcnow:
                player = None

        return player
