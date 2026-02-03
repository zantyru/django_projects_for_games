import logging
from django.conf import settings
from django.db import transaction
from django.db.utils import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View
from django.views.decorators.clickjacking import xframe_options_exempt
from game_triangle_racer import helpers
from game_triangle_racer.models import (
    Player, Resource, Costume, PlayerResource, PlayerCostume,
    ConfigOfInitialPlayerResource, ConfigOfInitialPlayerCostume
)


logger = logging.getLogger(__name__)


class GameClientView(View):
    """Sends a game client to a user."""

    @xframe_options_exempt
    def get(self, request, *args, **kwargs):

        referrer_domain = helpers.get_request_referrer_domain(request)
        logger.info(f'Запрос игрового клиента: домен реферера "{referrer_domain}".')

        # В режиме отладки разрешаем любой домен
        if settings.DEBUG and not referrer_domain:
            referrer_domain = 'vk.com'
            logger.debug('Режим отладки: установлен домен vk.com по умолчанию.')

        if referrer_domain == 'vk.com':
            logger.info(f'"{referrer_domain}" is permitted domain.')
            response = _make_response_for_vk(request)

        else:
            logger.warning(f'"{referrer_domain}" is NOT permitted domain!')
            response = HttpResponse()

        return response


def _make_response_for_vk(request):
    """Формирует ответ для VK платформы."""
    vk_app_secure_key = settings.VK_APP_SECURE_KEY
    if not vk_app_secure_key:
        logger.error('VK_APP_SECURE_KEY не настроен в settings.')
        return HttpResponse()

    urlvars_as_dict = request.GET.dict()

    platform = 'vk.com'
    platform_id = urlvars_as_dict.get('viewer_id', 0)

    if helpers.is_vk_session_valid(urlvars_as_dict, vk_app_secure_key) and helpers.try_int(platform_id) > 0:

        logger.info(f'Запрос принят: VK сессия валидна. Пользователь {platform_id}.')

        stamp = helpers.datetime_to_stamp(helpers.datetime_now_utc())

        with transaction.atomic():
            # Используем select_for_update для защиты от race conditions при создании игрока
            player = Player.objects.filter(
                platform=platform,
                platform_id=platform_id
            ).select_for_update().first()

            if not player:
                logger.info(f'Пользователь {platform_id} - новый игрок. Регистрация...')
                player = Player.objects.create(
                    platform=platform,
                    platform_id=platform_id,
                    regin_stamp=stamp
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

            player.login_stamp = stamp
            player.save(update_fields=['login_stamp'])

        response = render(
            request, 'game_triangle_racer/triangle_racer.html',
            context={
                'login_stamp': player.login_stamp,
                'platform': player.platform,
            }
        )

    else:

        logger.warning('Запрос отклонён: VK сессия не валидна.')

        response = HttpResponse()

    return response
