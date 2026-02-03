import os
import base64
from datetime import timedelta
from django.db import models
from game_triangle_racer import helpers


class Player(models.Model):
    """Представляет данные и состояние игрока в игре."""

    game_id = models.AutoField(primary_key=True)
    session_quasisecret = models.BigIntegerField(
        default=0,
        help_text="Секрет сессии для подписи запросов (разница между start_stamp и login_stamp)"
    )
    regin_stamp = models.BigIntegerField(
        default=0,
        help_text="Время регистрации в миллисекундах (timestamp * 1000)"
    )
    login_stamp = models.BigIntegerField(
        default=0,
        help_text="Время последнего входа в миллисекундах (timestamp * 1000)"
    )
    start_stamp = models.BigIntegerField(
        default=0,
        help_text="Время начала текущей сессии в миллисекундах (timestamp * 1000)"
    )
    token = models.CharField(
        max_length=32,
        unique=True,
        default=helpers.default_random_string,
        db_index=True,
        help_text="Токен для аутентификации API-запросов"
    )
    token_expiration = models.DateTimeField(
        default=helpers.datetime_now_utc,
        help_text="Срок действия токена"
    )
    platform = models.CharField(max_length=16, help_text="Платформа игрока (vk.com и т.п.)")
    platform_id = models.PositiveIntegerField(default=0, help_text="ID игрока на платформе")

    level = models.PositiveSmallIntegerField(default=0, help_text="Текущий уровень игрока")

    costumes = models.ManyToManyField('Costume', through='PlayerCostume')
    resources = models.ManyToManyField('Resource', through='PlayerResource')
    timers = models.ManyToManyField('Timer', through='PlayerTimer')

    class Meta:
        indexes = [
            models.Index(fields=['platform', 'platform_id'], name='player_platform_idx'),
        ]

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
        """Отзывает токен игрока, устанавливая срок действия в прошлое."""
        utcnow = helpers.datetime_now_utc()
        self.token_expiration = utcnow - timedelta(seconds=1)
        self.save(update_fields=['token_expiration'])

    @staticmethod
    def get_player_by_token(token):
        """Возвращает игрока по токену, если токен валиден и не истёк."""
        player = Player.objects.filter(token=token).first()

        if player:
            utcnow = helpers.datetime_now_utc()
            if player.token_expiration < utcnow:
                player = None

        return player

    @staticmethod
    def get_player_by_token_from_hex(hex_token):
        """Декодирует hex-токен из URL и возвращает игрока."""
        try:
            token = bytes.fromhex(hex_token).decode('utf-8')
        except (ValueError, UnicodeDecodeError):
            return None
        return Player.get_player_by_token(token)
