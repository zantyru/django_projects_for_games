import logging
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View
from django.views.decorators.clickjacking import xframe_options_exempt
from .. import helpers
from ..models import (
    Player, Resource, Costume, PlayerResource, PlayerCostume,
    ConfigOfInitialPlayerResource, ConfigOfInitialPlayerCostume
)


logger = logging.getLogger(__name__)


class GameClientView(View):
    """Sends a game client to a user."""

    @xframe_options_exempt
    def get(self, request, *args, **kwargs):

        referrer_domain = helpers.get_request_referrer_domain(request)
        logger.info(f'Game client has been requested: a referrer (domain) is "{referrer_domain}".')

        #@DEBUG +
        referrer_domain = 'vk.com'
        #@DEBUG -

        if referrer_domain == 'vk.com':
            logger.info(f'"{referrer_domain}" is permitted domain.')
            response = _make_response_for_vk(request)

        else:
            logger.warning(f'"{referrer_domain}" is NOT permitted domain!')
            response = HttpResponse()

        return response


def _make_response_for_vk(request):

    vk_app_secure_key = 'kFPuJIHCmuDuicPwprtP'  # @TODO Put all data in DB #@SMELL
    urlvars_as_dict = request.GET.dict()

    platform = 'vk.com'
    platform_id = urlvars_as_dict.get('viewer_id', 0)

    if helpers.is_vk_session_valid(urlvars_as_dict, vk_app_secure_key) and helpers.try_int(platform_id) > 0:

        logger.info(f'Request passed! VK session credentials is valid. User {platform_id}.')

        stamp = helpers.datetime_to_stamp(helpers.datetime_now_utc())

        player = Player.objects.filter(
            platform=platform,
            platform_id=platform_id
        ).first()

        if not player:
            logger.info(f'User {platform_id} is a new player! Registering...')
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
            PlayerResource.objects.bulk_create(player_resources)

        player.login_stamp = stamp
        player.save()

        response = render(
            request, 'game_triangle_racer/triangle_racer.html',
            context={
                'login_stamp': player.login_stamp,
                'platform': player.platform,
            }
        )

    else:

        logger.warning(f'Request rejected! VK session credentials is NOT valid.')

        response = HttpResponse()

    return response
