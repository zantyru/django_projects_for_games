import logging
from game_triangle_racer import helpers
from game_triangle_racer.models import Player, ShopSet, ShopSetComponent
from game_triangle_racer.views import interdata
from game_triangle_racer.views.base_api import BaseJsonSignedAPIView


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
#             "id": 1234
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
#             "id": 4321
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
#     "fromId": 4,
#     "toId": 16
# }
#
# Response JSON example 2:
# {
#     "sig": "<response signature symbols>",
#     "isSuccess": 1,
#     "shopSetsCount": 18,  # The count of all shop sets in database
#     "fromId": 4,
#     "toId": 16,
#     "shopSets": [
#         {
#             "id": 4
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
#             "id": 5
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


# Request JSON example 3:
# {
#     "sig": "<request signature symbols>",
#     "action": "buy",
#     "id": 4
# }
#
# Response JSON example 3-1:
# {
#     "sig": "<response signature symbols>",
#     "isSuccess": 1,
#     "purchase": {
#         "id": 4
#         "name": "<shop set 4 name>",
#         "price": 1234,
#         "components": [
#             {"name": "<shop set component 1 name>", "count": 23},
#             {"name": "<shop set component 2 name>", "count": 34},
#             {"name": "<shop set component 3 name>", "count": 56},
#             ...,
#         ]
#     }
# }
#
# Response JSON example 3-2:
# {
#     "sig": "<response signature symbols>",
#     "isSuccess": 0,
#     "purchase": {}
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
            n_from_id = helpers.try_int(data.get('fromId', -1), -1)
            n_to_id = helpers.try_int(data.get('toId', -1), -1)
            response = self.show_some(n_from_id, n_to_id)
        elif action == 'buy':
            n_id = helpers.try_int(data.get('id', -1), -1)
            response = self.buy(n_id)
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
                "id": shop_set.id,
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
    def show_some(n_from_id, n_to_id):
        """Возвращает наборы магазина в указанном диапазоне с оптимизацией запросов."""

        shop_sets_qs = ShopSet.objects.prefetch_related('shopsetcomponent_set__resource')
        shop_sets_count = shop_sets_qs.count()

        # Нормализация индексов
        n_from_id = max(0, min(n_from_id, shop_sets_count - 1)) if n_from_id >= 0 else 0
        n_to_id = max(0, min(n_to_id, shop_sets_count - 1)) if n_to_id >= 0 else 0

        # Меняем местами, если from > to
        if n_from_id > n_to_id:
            n_from_id, n_to_id = n_to_id, n_from_id

        shop_sets_qs = shop_sets_qs.order_by('pk')[n_from_id:n_to_id + 1]

        shop_sets = [
            {
                "id": shop_set.id,
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
                "fromId": n_from_id,
                "toId": n_to_id,
                "shopSets": shop_sets,
            }
        )

    @staticmethod
    def buy(n_id):

        pass
