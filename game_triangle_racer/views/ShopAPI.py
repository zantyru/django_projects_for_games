import logging
from .. import helpers
from ..models import Player, ShopSet, ShopSetComponent
from . import interdata
from .base_api import BaseJsonSignedAPIView


logger = logging.getLogger(__name__)


# Request JSON example 1:
# {
#     "sig": "<request signature symbols>",
#     "action": "showAll"
# }
#
# Response JSON example 1:
# {
#     "sig": "<response signature symbols>",
#     "isSuccess": 1,
#     "shopSetsCount": 18,  # The count of all shop sets in database
#     "shopSets": [
#         {
#             "name": "<shop set 1 name>",
#             "price": 1234,
#             "components": [
#                 {"name": "<shop set component 1 name>", "count": 23},
#                 {"name": "<shop set component 2 name>", "count": 34},
#                 {"name": "<shop set component 3 name>", "count": 56},
#                 ...,
#             ]
#         },
#         {
#             "name": "<shop set 2 name>",
#             "price": 1234,
#             "components": [
#                 {"name": "<shop set component 1 name>", "count": 98},
#                 {"name": "<shop set component 2 name>", "count": 76},
#                 {"name": "<shop set component 3 name>", "count": 54},
#                 ...,
#             ]
#         },
#     ]
# }
#


# Request JSON example 2:
# {
#     "sig": "<request signature symbols>",
#     "action": "showSome",
#     "from": 4,
#     "to": 16
# }
#
# Response JSON example 2:
# {
#     "sig": "<response signature symbols>",
#     "isSuccess": 1,
#     "shopSetsCount": 18,  # The count of all shop sets in database
#     "from": 4,
#     "to": 16,
#     "shopSets": [
#         {
#             "name": "<shop set 4 name>",
#             "price": 1234,
#             "components": [
#                 {"name": "<shop set component 1 name>", "count": 23},
#                 {"name": "<shop set component 2 name>", "count": 34},
#                 {"name": "<shop set component 3 name>", "count": 56},
#                 ...,
#             ]
#         },
#         {
#             "name": "<shop set 5 name>",
#             "price": 1234,
#             "components": [
#                 {"name": "<shop set component 1 name>", "count": 98},
#                 {"name": "<shop set component 2 name>", "count": 76},
#                 {"name": "<shop set component 3 name>", "count": 54},
#                 ...,
#             ]
#         },
#     ]
# }
#


class ShopAPI(BaseJsonSignedAPIView):
    """API-эндпоинт для работы с магазином."""

    def handle_request(self, data, player, *args, **kwargs):
        """Обрабатывает запрос к магазину."""
        action = data.get('action')

        if action == 'showAll':
            response = self.show_all()
        elif action == 'showSome':
            n_from = helpers.try_int(data.get('from', -1), -1)
            n_to = helpers.try_int(data.get('to', -1), -1)
            response = self.show_some(n_from, n_to)
        else:
            logger.warning(f'Неизвестное действие магазина: {action}')
            response = interdata.create_just_failure()

        logger.info(f'Запрос к магазину выполнен для игрока game_id={player.game_id}, действие: {action}.')
        return response

    @staticmethod
    def show_all():
        """Возвращает все наборы магазина с оптимизацией запросов."""
        # Оптимизация: предзагрузка компонентов одним запросом
        shop_sets_qs = ShopSet.objects.prefetch_related(
            'shopsetcomponent_set__resource'
        ).all()

        shop_sets = [
            {
                "name": shop_set.name,
                "price": shop_set.price,
                "components": [
                    {
                        "name": component.resource.name,
                        "count": component.count,
                    }
                    for component in shop_set.shopsetcomponent_set.all()
                ],
            }
            for shop_set in shop_sets_qs
        ]

        return interdata.create_by_extending(
            interdata.create_just_success(),
            **{
                "shopSetsCount": len(shop_sets),
                "shopSets": shop_sets,
            }
        )

    @staticmethod
    def show_some(n_from, n_to):
        """Возвращает наборы магазина в указанном диапазоне с оптимизацией запросов."""
        qs = ShopSet.objects.prefetch_related('shopsetcomponent_set__resource')
        shop_sets_count = qs.count()

        # Нормализация индексов
        n_from = max(0, min(n_from, shop_sets_count - 1)) if n_from >= 0 else 0
        n_to = max(0, min(n_to, shop_sets_count - 1)) if n_to >= 0 else 0

        # Меняем местами, если from > to
        if n_from > n_to:
            n_from, n_to = n_to, n_from

        shop_sets_qs = qs.order_by('pk')[n_from:n_to + 1]

        shop_sets = [
            {
                "name": shop_set.name,
                "price": shop_set.price,
                "components": [
                    {
                        "name": component.resource.name,
                        "count": component.count,
                    }
                    for component in shop_set.shopsetcomponent_set.all()
                ],
            }
            for shop_set in shop_sets_qs
        ]

        return interdata.create_by_extending(
            interdata.create_just_success(),
            **{
                "shopSetsCount": shop_sets_count,
                "from": n_from,
                "to": n_to,
                "shopSets": shop_sets,
            }
        )
