import logging
from django.db import transaction, IntegrityError
from game_triangle_racer.models import Player, PlayerResource, PlayerCostume, Costume, Resource
from game_triangle_racer import validators
from game_triangle_racer.views import interdata
from game_triangle_racer.views.base_api import BaseJsonSignedAPIView


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


class PushAPI(BaseJsonSignedAPIView):
    """API-эндпоинт для обновления игровой информации на сервере."""

    def handle_request(self, data, player, *args, **kwargs):
        """Обрабатывает запрос на обновление данных игрока."""
        (
            input_fields_0,
            input_fields_r,
            input_fields_c,
            _,  # Таймеры игнорируются
        ) = interdata.get_fields_as_dictionaries_or_nones(data)

        try:
            with transaction.atomic():
                # Используем select_for_update для защиты от race conditions
                player = Player.objects.select_for_update().get(pk=player.pk)
                
                self.update_player_common_data(player, input_fields_0)
                self.update_player_resources(player, input_fields_r)
                self.update_player_costumes(player, input_fields_c)

            response = interdata.create_by_extending(
                interdata.create_just_success(),
            )

            logger.info(f'Запрос на обновление данных выполнен для игрока game_id={player.game_id}.')
        except ValueError as e:
            # Ошибка валидации
            logger.warning(f'Ошибка валидации для игрока {player.game_id}: {e}')
            response = interdata.create_validation_error(str(e))
        except IntegrityError as e:
            # Ошибка целостности БД
            logger.error(f'Ошибка целостности БД для игрока {player.game_id}: {e}')
            response = interdata.create_just_failure()
            response[interdata.FIELD_ERROR_MESSAGE] = 'Ошибка при сохранении данных.'

        return response

    @staticmethod
    def update_player_common_data(player, input_fields_0):
        """Обновляет общие данные игрока (уровень и т.п.)."""
        if input_fields_0 is None:
            return

        updated = False
        for k, v in input_fields_0.items():
            if k == interdata.PLAYER_LEVEL:
                # Валидация уровня
                is_valid, error_message = validators.validate_level(v)
                if not is_valid:
                    logger.warning(f'Невалидный уровень {v} для игрока {player.game_id}: {error_message}')
                    raise ValueError(error_message)
                player.level = v
                updated = True

        if updated:
            player.save(update_fields=['level'])

    @staticmethod
    def update_player_resources(player, input_fields_r):
        """Обновляет ресурсы игрока. Оптимизировано для пакетного сохранения."""
        if input_fields_r is None:
            return

        if not input_fields_r:
            return

        # Получаем все нужные ресурсы одним запросом
        resource_names = list(input_fields_r.keys())
        resources = {r.name: r for r in Resource.objects.filter(name__in=resource_names)}

        # Получаем существующие PlayerResource одним запросом
        existing_resources = PlayerResource.objects.filter(
            player=player,
            resource__name__in=resource_names
        ).select_related('resource')

        existing_dict = {pr.resource.name: pr for pr in existing_resources}
        resources_to_update = []
        resources_to_create = []

        for resource_name, count in input_fields_r.items():
            if resource_name not in resources:
                logger.warning(f'Ресурс "{resource_name}" не найден в базе данных.')
                raise ValueError(f'Ресурс "{resource_name}" не найден в базе данных.')

            # Валидация количества ресурса
            is_valid, error_message = validators.validate_resource_count(count)
            if not is_valid:
                logger.warning(f'Невалидное количество ресурса {resource_name}={count} для игрока {player.game_id}: {error_message}')
                raise ValueError(f'Ресурс "{resource_name}": {error_message}')

            if resource_name in existing_dict:
                # Обновляем существующий
                pr = existing_dict[resource_name]
                pr.count = count
                resources_to_update.append(pr)
            else:
                # Создаём новый
                resources_to_create.append(
                    PlayerResource(player=player, resource=resources[resource_name], count=count)
                )

        # Пакетные операции
        try:
            if resources_to_update:
                PlayerResource.objects.bulk_update(resources_to_update, ['count'])
            if resources_to_create:
                PlayerResource.objects.bulk_create(resources_to_create)
        except IntegrityError as e:
            logger.error(f'Ошибка при bulk операциях с ресурсами для игрока {player.game_id}: {e}')
            raise

    @staticmethod
    def update_player_costumes(player, input_fields_c):
        """Обновляет костюмы игрока. True - добавить/оставить, False - удалить."""
        if input_fields_c is None:
            return

        if not input_fields_c:
            return

        # Получаем все нужные костюмы одним запросом
        costume_names = list(input_fields_c.keys())
        costumes = {c.name: c for c in Costume.objects.filter(name__in=costume_names)}

        # Получаем существующие PlayerCostume одним запросом
        existing_costumes = PlayerCostume.objects.filter(
            player=player,
            costume__name__in=costume_names
        ).select_related('costume')

        existing_names = {pc.costume.name for pc in existing_costumes}
        costumes_to_create = []
        costumes_to_delete = []

        for costume_name, should_have in input_fields_c.items():
            if costume_name not in costumes:
                logger.warning(f'Костюм "{costume_name}" не найден в базе данных.')
                raise ValueError(f'Костюм "{costume_name}" не найден в базе данных.')

            if should_have and costume_name not in existing_names:
                # Нужно добавить
                costumes_to_create.append(
                    PlayerCostume(player=player, costume=costumes[costume_name])
                )
            elif not should_have and costume_name in existing_names:
                # Нужно удалить
                pc = next(pc for pc in existing_costumes if pc.costume.name == costume_name)
                costumes_to_delete.append(pc.pk)

        # Пакетные операции
        try:
            if costumes_to_create:
                PlayerCostume.objects.bulk_create(costumes_to_create)
            if costumes_to_delete:
                PlayerCostume.objects.filter(pk__in=costumes_to_delete).delete()
        except IntegrityError as e:
            logger.error(f'Ошибка при bulk операциях с костюмами для игрока {player.game_id}: {e}')
            raise
