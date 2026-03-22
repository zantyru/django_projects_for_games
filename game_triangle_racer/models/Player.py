import os
import base64
import logging
from datetime import timedelta
from django.db import models
from django.db.utils import IntegrityError
from game_triangle_racer import helpers
from game_triangle_racer.models import (
    PlayerResource,
    ConfigOfInitialPlayerResource
)


logger = logging.getLogger(__name__)


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

    @staticmethod
    def create_and_get_new_player(platform, platform_id, regin_stamp):

        player = Player.objects.create(
            platform=platform,
            platform_id=platform_id,
            regin_stamp=regin_stamp
        )

        player_resources = []

        for row in ConfigOfInitialPlayerResource.objects.all().iterator():
            player_resources.append(
                PlayerResource(player=player, resource=row.resource, count=row.initial_count)
            )

        if player_resources:
            try:
                PlayerResource.objects.bulk_create(player_resources)
            except IntegrityError as e:
                logger.error(f'Ошибка при создании начальных ресурсов для игрока {player.platform_id}: {e}')
                raise

        return player
