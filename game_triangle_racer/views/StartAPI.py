import logging
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .. import helpers
from ..models import Player
from . import interdata


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class StartAPI(View):
    """An API endpoint for starting game session. Sends token."""

    def post(self, request, *args, **kwargs):

        if request.content_type != 'application/json':
            logger.warning('Start request rejected: no JSON.')
            response = interdata.create_only_json_allowed_error()

        else:
            data = interdata.from_json(request.body)
            if not data:
                logger.warning('Start request rejected: wrong JSON.')
                response = interdata.create_wrong_json_error()

            else:
                platform = interdata.get_platform(data)
                logger.info(f'Start request from \'{platform}\': {data}')

                response = interdata.create_just_failure()
                if platform == 'vk.com':
                    response = _make_response_for_vk(data)

        return JsonResponse(response)


def _make_response_for_vk(data):

    vk_app_secure_key = 'kFPuJIHCmuDuicPwprtP'  # @TODO Put all data in DB #@SMELL
    response = interdata.create_just_failure()

    platform = interdata.get_platform(data)
    platform_id = interdata.get_platform_id(data)
    platform_api_id = interdata.get_platform_api_id(data)
    platform_auth_key = interdata.get_platform_auth_key(data)

    d = {
        helpers.FIELD_NAME_VK_VIEWER_ID: platform_id,
        helpers.FIELD_NAME_VK_API_ID: platform_api_id,
        helpers.FIELD_NAME_VK_AUTH_KEY: platform_auth_key,
    }

    if helpers.is_vk_session_valid(d, vk_app_secure_key):
        player = Player.objects.filter(
            platform=platform,
            platform_id=platform_id
        ).first()

        if player:
            start_stamp = helpers.datetime_to_stamp(helpers.datetime_now_utc())
            response = interdata.create_by_extending(
                interdata.create_just_success(),
                **{  #@TODO Rearchitect
                    interdata.FIELD_TOKEN: player.get_token(),
                    interdata.FIELD_T: start_stamp,
                }
            )

            player.start_stamp = start_stamp
            player.session_quasisecret = start_stamp - player.login_stamp

            player.save()
            logger.info(f'A token (game_id = {player.game_id}) has been processed. Response data: {response}')

        else:
            logger.warning('Token processing failed.')

    else:
        logger.warning('Session is not valid.')

    return response
