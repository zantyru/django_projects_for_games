import logging
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .. import helpers
from ..models import Player, PlayerResource
from . import interdata


logger = logging.getLogger(__name__)


# Request JSON example:
# {
#     "sig": "<response signature symbols>",
#     "0": {
#         "gameID": 5262235,  ## Will be ignored
#         "level": 12
#     },
#     "r": {
#         "stars": 1,
#         "lives": 2,
#         "chances": 7,
#         "coins": 1000
#     },
#     "c": {
#         "<costume name>": true,
#         "<costume name>": false,
#         "<costume name>": true
#     }
#     "z": {  ## Any timer data will be ignored
#         "<timer name>": 0,
#         "<timer name>": 453,
#     }
# }
#
# Response JSON example:
# {
#     "sig": "<response signature symbols>",
#     "isSuccess": 1,
# }
#
#
#
#
#
#
#
#
#
#
#
#
#
#


@method_decorator(csrf_exempt, name='dispatch')
class PushAPI(View):
    """An API endpoint for updating game information on server."""

    def post(self, request, token, *args, **kwargs):

        response = interdata.create_just_failure()

        try:
            token = bytes.fromhex(token).decode('utf-8')
        except (ValueError, UnicodeDecodeError):
            token = ''

        if request.content_type != 'application/json':
            logger.warning('Push request rejected: no JSON.')
            response = interdata.create_only_json_allowed_error()

        else:
            data = interdata.from_json(request.body)

            if not data:
                logger.warning(f'Push request rejected: wrong JSON: {data}')
                response = interdata.create_wrong_json_error()

            else:
                logger.info(f'Incoming push request data: {data}. Token \'{token}\'.')

                player = Player.objects.filter(
                    token=token,
                    state=Player.State.GAMING
                ).first()

                if player:
                    session_quasisecret = str(player.session_quasisecret)

                    if interdata.is_signed_well(data, session_quasisecret):
                        (
                            input_fields_0,
                            input_fields_r,
                            input_fields_c,
                            _,  # Ignoring timers
                        ) = interdata.get_fields_as_dictionaries_or_nones(data)

                        self.update_player_common_data(player, input_fields_0)
                        self.update_player_resources(player, input_fields_r)
                        self.update_player_costumes(player, input_fields_c)
                        #

                        response = interdata.create_by_extending(
                            interdata.create_just_success(),
                            #
                            #
                            #
                            #
                        )

                        logger.info(f'Push request completed: token \'{token}\'. Response data: {response}')

                    else:
                        logger.warning(
                            f'Push request can not be completed:'
                            f' player with token \'{token}\' has been received wrong signed data {data}.'
                            f' Response data: {response}'
                        )

                    interdata.signify(response, session_quasisecret)

                else:
                    logger.info(f'Push request can not be completed: player with token \'{token}\' does not exist.'
                                f' Response data: {response}')

        return JsonResponse(response)

    @staticmethod
    def update_player_common_data(player, input_fields_0):

        if input_fields_0 is None:
            return

        for k, v in input_fields_0.items():
            if k == interdata.PLAYER_LEVEL:
                player.level = v  # TODO Проверить django F() и Q()

        player.save()

    @staticmethod
    def update_player_resources(player, input_fields_r):

        if input_fields_r is None:
            return

        for k, v in input_fields_r.items():
            player_resource = PlayerResource.objects.filter(
                player=player,
                resource__name=k
            ).first()
            if player_resource:
                player_resource.count = v
                player_resource.save()  #@CHECK Bulk save?
            else:
                pass  # @TODO Создание новой записи о ресурсе игрока

    @staticmethod
    def update_player_costumes(player, input_fields_c):

        if input_fields_c is None:
            return

        for k, v in input_fields_c.items():
            pass  # @TODO
