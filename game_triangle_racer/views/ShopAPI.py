import logging
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .. import helpers
from ..models import Player, ShopSet, ShopSetComponent
from . import interdata


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


@method_decorator(csrf_exempt, name='dispatch')
class ShopAPI(View):

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
                logger.warning(f'Shop request rejected: wrong JSON: {data}')
                response = interdata.create_wrong_json_error()

            else:
                logger.info(f'Incoming shop request data: {data}. Token \'{token}\'.')

                player = Player.objects.filter(
                    token=token,
                    state=Player.State.GAMING  # Player.State.SHOPPING ?
                ).first()

                if player:
                    session_quasisecret = str(player.session_quasisecret)

                    if interdata.is_signed_well(data, session_quasisecret):

                        action = data.get('action')  #@TODO interdata or shopinterdata
                        if action == 'showAll':
                            response = self.show_all()

                        elif action == 'showSome':
                            n_from = helpers.try_int(data.get('from', -1), -1)
                            n_to = helpers.try_int(data.get('to', -1), -1)
                            response = self.show_some(n_from, n_to)

                        ...

                        logger.info(f'Shop request completed: token \'{token}\'. Response data: {response}')

                    else:
                        logger.warning(
                            f'Shop request can not be completed:'
                            f' player with token \'{token}\' has been received wrong signed data {data}.'
                            f' Response data: {response}'
                        )

                    interdata.signify(response, session_quasisecret)

                else:
                    logger.info(f'Shop request can not be completed: player with token \'{token}\' does not exist.'
                                f' Response data: {response}')

        return JsonResponse(response)

    @staticmethod
    def show_all():

        #@TODO Использовать list и dict comprehension

        shop_sets = []

        for q_shop_set in ShopSet.objects.all():
            shop_set = {
                "name": q_shop_set.name,
                "price": q_shop_set.price,
                "components": [],
            }

            components = shop_set["components"]
            for q_shop_set_component in ShopSetComponent.objects.filter(shop_set=q_shop_set):
                shop_set_component = {
                    "name": q_shop_set_component.resource.name,
                    "count": q_shop_set_component.count,
                }
                components.append(shop_set_component)

            shop_sets.append(shop_set)

        return interdata.create_by_extending(
            interdata.create_just_success(),
            **{
                "shopSetsCount": len(shop_sets),
                "shopSets": shop_sets,
            }
        )

    @staticmethod
    def show_some(n_from, n_to):

        # @TODO Использовать list и dict comprehension

        shop_sets = []

        qs = ShopSet.objects.all()
        shop_sets_count = qs.count()

        if n_from < 0:
            n_from = 0

        if n_to < 0:
            n_to = 0

        if n_from >= shop_sets_count:
            n_from = shop_sets_count - 1

        if n_to >= shop_sets_count:
            n_to = shop_sets_count - 1

        for q_shop_set in qs.order_by('pk')[n_from:n_to+1]:
            shop_set = {
                "name": q_shop_set.name,
                "price": q_shop_set.price,
                "components": [],
            }

            components = shop_set["components"]
            for q_shop_set_component in ShopSetComponent.objects.filter(shop_set=q_shop_set):
                shop_set_component = {
                    "name": q_shop_set_component.resource.name,
                    "count": q_shop_set_component.count,
                }
                components.append(shop_set_component)

            shop_sets.append(shop_set)

        return interdata.create_by_extending(
            interdata.create_just_success(),
            **{
                "shopSetsCount": len(shop_sets),
                "shopSets": shop_sets,
            }
        )
