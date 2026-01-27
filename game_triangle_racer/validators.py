"""Валидаторы для проверки игровых данных."""

import logging
from ..models.Config import Config

logger = logging.getLogger(__name__)

# Константы валидации (можно переопределить через Config модель)
MAX_LEVEL = 9999
MAX_RESOURCE_COUNT = 999999999
MIN_RESOURCE_COUNT = 0


def validate_level(level):
    """
    Валидирует уровень игрока.
    
    Args:
        level: Уровень для проверки
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(level, int):
        return False, "Уровень должен быть целым числом"
    
    if level < 0:
        return False, "Уровень не может быть отрицательным"
    
    max_level = _get_max_level()
    if level > max_level:
        return False, f"Уровень не может превышать {max_level}"
    
    return True, None


def validate_resource_count(count):
    """
    Валидирует количество ресурса.
    
    Args:
        count: Количество для проверки
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(count, (int, float)):
        return False, "Количество ресурса должно быть числом"
    
    count = int(count)
    
    if count < MIN_RESOURCE_COUNT:
        return False, f"Количество ресурса не может быть меньше {MIN_RESOURCE_COUNT}"
    
    max_count = _get_max_resource_count()
    if count > max_count:
        return False, f"Количество ресурса не может превышать {max_count}"
    
    return True, None


def _get_max_level():
    """Получает максимальный уровень из конфигурации или использует значение по умолчанию."""
    try:
        config = Config.objects.first()
        if config and hasattr(config, 'max_level'):
            return config.max_level
    except Exception as e:
        logger.warning(f'Ошибка при получении max_level из конфигурации: {e}')
    return MAX_LEVEL


def _get_max_resource_count():
    """Получает максимальное количество ресурса из конфигурации или использует значение по умолчанию."""
    try:
        config = Config.objects.first()
        if config and hasattr(config, 'max_resource_count'):
            return config.max_resource_count
    except Exception as e:
        logger.warning(f'Ошибка при получении max_resource_count из конфигурации: {e}')
    return MAX_RESOURCE_COUNT
