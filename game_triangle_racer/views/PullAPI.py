import logging
from django.db import transaction
from django.db.models import Prefetch
from django_projects.game_triangle_racer.models import Player, PlayerResource, PlayerCostume, PlayerTimer, Resource, Costume, Timer
from django_projects.game_triangle_racer.views import interdata
from django_projects.game_triangle_racer.views.base_api import BaseJsonSignedAPIView


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


class PullAPI(BaseJsonSignedAPIView):
    """API-эндпоинт для получения игровой информации с сервера."""

    def handle_request(self, data, player, *args, **kwargs):
        """Обрабатывает запрос на получение данных игрока."""
        (
            input_fields_0,
            input_fields_r,
            input_fields_c,
            input_fields_z,
        ) = interdata.get_fields_as_lists_or_nones(data)

        output_fields_0 = self.read_player_common_data(player, input_fields_0)
        output_fields_r = self.read_player_resources(player, input_fields_r)
        output_fields_c = self.read_player_costumes(player, input_fields_c)
        output_fields_z = self.read_player_timers(player, [] if input_fields_z is None else input_fields_z)

        response = interdata.create_by_field_compositing(
            interdata.create_just_success(),
            field_0=output_fields_0,
            field_r=output_fields_r,
            field_c=output_fields_c,
            field_z=output_fields_z,
        )

        logger.info(f'Запрос на получение данных выполнен для игрока game_id={player.game_id}.')
        return response

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
        """Читает ресурсы игрока одним запросом."""
        if input_fields_r is None:
            return None

        # Оптимизация: один запрос вместо N запросов
        player_resources = PlayerResource.objects.filter(
            player=player,
            resource__name__in=input_fields_r
        ).select_related('resource')

        resource_dict = {pr.resource.name: pr.count for pr in player_resources}
        output_fields_r = {name: resource_dict.get(name, 0) for name in input_fields_r}

        return output_fields_r

    @staticmethod
    def read_player_costumes(player, input_fields_c):
        """Читает костюмы игрока. Если список пуст ([]), возвращает все костюмы."""
        if input_fields_c is None:
            return None

        if input_fields_c:
            # Запрошены конкретные костюмы
            player_costumes = PlayerCostume.objects.filter(
                player=player,
                costume__name__in=input_fields_c
            ).select_related('costume')

            costume_names = {pc.costume.name for pc in player_costumes}
            output_fields_c = {name: name in costume_names for name in input_fields_c}
        else:
            # Пустой список означает "вернуть все костюмы игрока"
            player_costumes = PlayerCostume.objects.filter(player=player).select_related('costume')
            output_fields_c = {pc.costume.name: True for pc in player_costumes}

        return output_fields_c

    @staticmethod
    def read_player_timers(player, input_fields_z):
        """Читает таймеры игрока. Обновляет их состояние и удаляет истёкшие."""
        if input_fields_z is None:
            return None

        if input_fields_z:
            # Запрошены конкретные таймеры
            with transaction.atomic():
                player_timers = PlayerTimer.objects.filter(
                    player=player,
                    timer__name__in=input_fields_z
                ).select_related('timer').select_for_update()

                # Обновляем все таймеры
                timers_to_update = []
                timers_to_delete = []
                output_fields_z = {}

                for player_timer in player_timers:
                    player_timer.update()
                    if player_timer.state == PlayerTimer.State.EXPIRED:
                        timers_to_delete.append(player_timer.pk)
                    elif player_timer.state != PlayerTimer.State.PLANNED:
                        output_fields_z[player_timer.timer.name] = player_timer.remaining
                        timers_to_update.append(player_timer)

                # Пакетные операции
                if timers_to_update:
                    PlayerTimer.objects.bulk_update(timers_to_update, ['state', 'remaining', 'start_datetime'])
                if timers_to_delete:
                    PlayerTimer.objects.filter(pk__in=timers_to_delete).delete()

                # Добавляем нули для запрошенных, но не найденных таймеров
                found_names = {pt.timer.name for pt in player_timers}
                for name in input_fields_z:
                    if name not in found_names:
                        output_fields_z[name] = 0

        else:
            # Пустой список означает "вернуть все таймеры игрока"
            with transaction.atomic():
                player_timers = PlayerTimer.objects.filter(player=player).select_related('timer').select_for_update()

                # Обновляем все таймеры
                timers_to_update = []
                timers_to_delete = []

                for player_timer in player_timers:
                    player_timer.update()
                    if player_timer.state == PlayerTimer.State.EXPIRED:
                        timers_to_delete.append(player_timer.pk)
                    else:
                        timers_to_update.append(player_timer)

                # Пакетные операции
                if timers_to_update:
                    PlayerTimer.objects.bulk_update(timers_to_update, ['state', 'remaining', 'start_datetime'])
                if timers_to_delete:
                    PlayerTimer.objects.filter(pk__in=timers_to_delete).delete()

                output_fields_z = {
                    player_timer.timer.name: player_timer.remaining
                    for player_timer in player_timers
                    if player_timer.state != PlayerTimer.State.PLANNED
                }

        return output_fields_z
