import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from game_triangle_racer.models import Player
from game_triangle_racer.views import interdata

logger = logging.getLogger(__name__)


class BaseJsonSignedAPIView(APIView):
    """Базовый класс для JSON API с проверкой подписи и токена."""

    def post(self, request, *args, **kwargs):
        """Обрабатывает POST-запрос с JSON-телом."""
        # Проверка Content-Type
        if request.content_type != 'application/json':
            logger.warning('Запрос отклонён: требуется JSON.')
            response = interdata.create_only_json_allowed_error()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        # Парсинг JSON
        data = interdata.from_json(request.body)
        if not data:
            logger.warning('Запрос отклонён: некорректный JSON.')
            response = interdata.create_wrong_json_error()
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        # Получение токена из URL (если требуется)
        token_hex = kwargs.get('token')
        if token_hex:
            player = Player.get_player_by_token_from_hex(token_hex)
        else:
            player = None

        # Логирование (без чувствительных данных)
        safe_data = self._mask_sensitive_data(data.copy())
        logger.info(f'Входящий запрос: {safe_data}. Токен: {"***" if token_hex else "нет"}.')

        if not player:
            logger.info(f'Запрос отклонён: игрок с токеном не найден или токен истёк.')
            response = interdata.create_just_failure()
            interdata.signify(response, '')
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

        # Проверка подписи
        session_quasisecret = str(player.session_quasisecret)
        if not interdata.is_signed_well(data, session_quasisecret):
            logger.warning(
                f'Запрос отклонён: неверная подпись для игрока {player.game_id}.'
            )
            response = interdata.create_just_failure()
            interdata.signify(response, session_quasisecret)
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

        # Вызов метода обработки запроса
        try:
            response = self.handle_request(data, player, *args, **kwargs)
            interdata.signify(response, session_quasisecret)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f'Ошибка при обработке запроса: {e}', exc_info=True)
            response = interdata.create_just_failure()
            interdata.signify(response, session_quasisecret)
            return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def handle_request(self, data, player, *args, **kwargs):
        """Обрабатывает запрос после всех проверок. Должен быть переопределён в наследниках."""
        raise NotImplementedError("Метод handle_request должен быть переопределён.")

    @staticmethod
    def _mask_sensitive_data(data):
        """Маскирует чувствительные данные в логах."""
        if isinstance(data, dict):
            masked = data.copy()
            if 'sig' in masked:
                masked['sig'] = '***'
            if 'platformAuthKey' in masked:
                masked['platformAuthKey'] = '***'
            return masked
        return data
