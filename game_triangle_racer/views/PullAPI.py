import logging
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .. import helpers
from ..models import Player, PlayerResource, PlayerCostume, PlayerTimer
from . import interdata


logger = logging.getLogger(__name__)


# Request JSON example:
# {
#     "sig": "<request signature symbols>",
#     "0": [
#         "level"
#     ],
#     "r": [
#         "coins",
#         "lives",
#         "stars",
#         "chances"
#     ],
#     "c": [],  ## Empty list means getting all data
#     "z": [
#         "<timer name>",
#         "<timer name>"
#     ]
# }
#
# Response JSON example:
# {
#     "sig": "<response signature symbols>",
#     "isSuccess": 1,
#     "0": {
#         "gameID": 5262235,
#         "level"
#     },
#     "r": {
#         "stars": 0,
#         "lives": 2,
#         "chances": 7,
#         "coins": 1000
#     },
#     "c": {
#         "<costume name>": true,  ## 'true' means availability
#         "<costume name>": false
#     }
#     "z": {
#         "<timer name>": 23001,  ## milliseconds
#         "<timer name>": 1234
#     }
# }
#


@method_decorator(csrf_exempt, name='dispatch')
class PullAPI(View):
    """An API endpoint for retrieving game information from server."""

    def post(self, request, token, *args, **kwargs):

        response = interdata.create_just_failure()

        try:
            token = bytes.fromhex(token).decode('utf-8')
        except (ValueError, UnicodeDecodeError):
            token = ''

        if request.content_type != 'application/json':
            logger.warning('Pull request rejected: no JSON.')
            response = interdata.create_only_json_allowed_error()

        else:
            data = interdata.from_json(request.body)

            if not data:
                logger.warning(f'Pull request rejected: wrong JSON: {data}')
                response = interdata.create_wrong_json_error()

            else:
                logger.info(f'Incoming pull request data: {data}. Token \'{token}\'.')

                player = Player.objects.filter(token=token).first()

                if player:
                    session_quasisecret = str(player.session_quasisecret)

                    if interdata.is_signed_well(data, session_quasisecret):
                        (
                            input_fields_0,
                            input_fields_r,
                            input_fields_c,
                            input_fields_z,
                        ) = interdata.get_fields_as_lists_or_nones(data)

                        output_fields_0 = self.read_player_common_data(player, input_fields_0)
                        output_fields_r = self.read_player_resources(player, input_fields_r)
                        output_fields_c = self.read_player_costumes(player, input_fields_c)
                        output_fields_z = self.read_player_timers(player, [] if input_fields_z is None else input_fields_z)  #@DEBUG

                        response = interdata.create_by_field_compositing(
                            interdata.create_just_success(),
                            field_0=output_fields_0,
                            field_r=output_fields_r,
                            field_c=output_fields_c,
                            field_z=output_fields_z,
                        )

                        logger.info(f'Pull request completed: token \'{token}\'. Response data: {response}')

                    else:
                        logger.warning(
                            f'Pull request can not be completed:'
                            f' player with token \'{token}\' has been received wrong signed data {data}.'
                            f' Response data: {response}'
                        )

                    interdata.signify(response, session_quasisecret)

                else:
                    logger.info(f'Pull request can not be completed: player with token \'{token}\' does not exist.'
                                f' Response data: {response}')

        return JsonResponse(response)

    @staticmethod
    def read_player_common_data(player, input_fields_0):

        if input_fields_0 is None:
            return None

        output_fields_0 = {}
        for e in input_fields_0:
            if e == interdata.PLAYER_LEVEL:
                output_fields_0[e] = player.level
        output_fields_0[interdata.PLAYER_ID] = player.game_id  # Always available for game client

        return output_fields_0

    @staticmethod
    def read_player_resources(player, input_fields_r):

        if input_fields_r is None:
            return None

        output_fields_r = {}
        for e in input_fields_r:
            player_resource = PlayerResource.objects.filter(
                player=player,
                resource__name=e
            ).first()
            output_fields_r[e] = player_resource.count if player_resource else 0

        return output_fields_r

    @staticmethod
    def read_player_costumes(player, input_fields_c):

        if input_fields_c is None:
            return None

        if input_fields_c:  # Can be []. It is necessary to distinguish between [] and None
            output_fields_c = {}
            for e in input_fields_c:
                player_costume = PlayerCostume.objects.filter(
                    player=player,
                    costume__name=e
                ).first()
                output_fields_c[e] = bool(player_costume)
        else:  # @TEST_IT
            output_fields_c = {
                player_costume.costume.name: True
                for player_costume in PlayerCostume.objects.filter(player=player)
            }

        return output_fields_c

    @staticmethod
    def read_player_timers(player, input_fields_z):

        if input_fields_z is None:
            return None

        if input_fields_z:  # Can be []. It is necessary to distinguish between [] and None
            output_fields_z = {}
            for e in input_fields_z:
                player_timer = PlayerTimer.objects.filter(
                    player=player,
                    timer__name=e
                ).first()
                if player_timer:
                    player_timer.update()
                    if player_timer.state != PlayerTimer.State.PLANNED:
                        output_fields_z[e] = player_timer.remaining
                    if player_timer.state == PlayerTimer.State.EXPIRED:
                        player_timer.delete()
        else:  #@TEST_IT  #@REFACTOR

            player_timers = PlayerTimer.objects.filter(player=player)

            for player_timer in player_timers:
                player_timer.update()

            output_fields_z = {
                player_timer.timer.name: player_timer.remaining
                for player_timer in player_timers
                if player_timer.state != PlayerTimer.State.PLANNED
            }

            for player_timer in player_timers:
                if player_timer.state == PlayerTimer.State.EXPIRED:
                    player_timer.delete()

        return output_fields_z
