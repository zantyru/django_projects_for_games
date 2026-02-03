import logging
from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from game_triangle_racer import helpers
from game_triangle_racer.models import Player
from game_triangle_racer.views import interdata


logger = logging.getLogger(__name__)


class StartAPI(APIView):
    """API-эндпоинт для начала игровой сессии. Выдаёт токен."""

    def post(self, request, *args, **kwargs):
        """Обрабатывает запрос на начало сессии."""
        if request.content_type != 'application/json':
            logger.warning('Запрос отклонён: требуется JSON.')
            response = interdata.create_only_json_allowed_error()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        data = interdata.from_json(request.body)
        if not data:
            logger.warning('Запрос отклонён: некорректный JSON.')
            response = interdata.create_wrong_json_error()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        platform = interdata.get_platform(data)
        safe_data = self._mask_sensitive_data(data.copy())
        logger.info(f'Запрос на начало сессии от платформы \'{platform}\': {safe_data}')

        response = interdata.create_just_failure()
        if platform == 'vk.com':
            response = self._make_response_for_vk(data)

        return Response(response, status=status.HTTP_200_OK)

    def _make_response_for_vk(self, data):
        """Обрабатывает запрос от VK платформы."""
        vk_app_secure_key = settings.VK_APP_SECURE_KEY
        if not vk_app_secure_key:
            logger.error('VK_APP_SECURE_KEY не настроен в settings.')
            return interdata.create_just_failure()

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
            with transaction.atomic():
                # Используем select_for_update для защиты от race conditions
                player = Player.objects.filter(
                    platform=platform,
                    platform_id=platform_id
                ).select_for_update().first()

                if player:
                    start_stamp = helpers.datetime_to_stamp(helpers.datetime_now_utc())
                    response = interdata.create_by_extending(
                        interdata.create_just_success(),
                        **{
                            interdata.FIELD_TOKEN: player.get_token(),
                            interdata.FIELD_T: start_stamp,
                        }
                    )

                    player.start_stamp = start_stamp
                    player.session_quasisecret = start_stamp - player.login_stamp
                    player.save(update_fields=['start_stamp', 'session_quasisecret', 'token', 'token_expiration'])

                    logger.info(f'Токен выдан для игрока game_id={player.game_id}.')

                else:
                    logger.warning('Обработка токена не удалась: игрок не найден.')

        else:
            logger.warning('Сессия VK не валидна.')

        return response

    @staticmethod
    def _mask_sensitive_data(data):
        """Маскирует чувствительные данные в логах."""
        if isinstance(data, dict):
            masked = data.copy()
            if 'platformAuthKey' in masked:
                masked['platformAuthKey'] = '***'
            return masked
        return data
