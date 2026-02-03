import json
import hashlib
from game_triangle_racer import helpers


YES = 1
NOO = 0
EMPTY = ''

# Имена секций в JSON-запросах/ответах
FIELD_0 = '0'  # Общие игровые данные игрока (уровень и т.п.)
FIELD_R = 'r'  # Ресурсы игрока
FIELD_C = 'c'  # Костюмы игрока
FIELD_Z = 'z'  # Таймеры игрока

# Names of technical fields (no section)
FIELD_IS_SUCCESS = 'isSuccess'
FIELD_SIGNATURE = 'sig'
FIELD_ERROR_CODE = 'errorCode'
FIELD_ERROR_MESSAGE = 'errorMessage'
FIELD_PLATFORM = 'platform'
FIELD_PLATFORM_ID = 'platformID'
FIELD_PLATFORM_API_ID = 'platformAPIID'
FIELD_PLATFORM_AUTH_KEY = 'platformAuthKey'
FIELD_TOKEN = 'token'
FIELD_T = 't'

# Names of fields about common gameplay data (section FIELD_0)
PLAYER_ID = 'playerID'
PLAYER_LEVEL = 'level'


# Tools


def from_json(json_object):
    """Парсит JSON-строку или bytes. Возвращает словарь или пустой словарь при ошибке."""
    try:
        if isinstance(json_object, bytes):
            json_object = json_object.decode('utf-8')
        data = json.loads(json_object)
    except (json.JSONDecodeError, UnicodeDecodeError):
        data = {}
    return data


def signify(struct, secret):
    """
    Добавляет подпись к структуре данных.
    
    Подпись вычисляется как MD5 от строкового представления структуры
    (через stringify) + секрет. Подпись добавляется в поле 'sig'.
    """
    if not isinstance(struct, dict):
        raise ValueError("Первый параметр должен быть словарём.")

    struct[FIELD_SIGNATURE] = hashlib.md5(
        f'{helpers.stringify(struct)}{secret}'.encode('utf-8')
    ).hexdigest()


def is_successful(struct):
    return struct.get(FIELD_IS_SUCCESS, NOO) == YES


def is_signed_well(struct, secret):
    """
    Проверяет корректность подписи в структуре данных.
    
    Вычисляет подпись от структуры без поля 'sig' и сравнивает с полученной подписью.
    """
    received_sig = struct.get(FIELD_SIGNATURE, '')
    computed_sig = hashlib.md5(
        f'{helpers.stringify({k: v for k, v in struct.items() if k != FIELD_SIGNATURE})}{secret}'.encode('utf-8')
    ).hexdigest()

    return received_sig == computed_sig


# Structure creators


def create(**kwargs):
    return {**kwargs}  # Copying (light version)


def create_by_extending(struct, **kwargs):
    return {**struct, **kwargs}


def create_by_field_compositing(struct, field_0=None, field_r=None, field_c=None, field_z=None):

    result = {**struct}

    if field_0 is not None:
        result[FIELD_0] = field_0

    if field_r is not None:
        result[FIELD_R] = field_r

    if field_c is not None:
        result[FIELD_C] = field_c

    if field_z is not None:
        result[FIELD_Z] = field_z

    return result


def create_just_success():
    return {
        FIELD_IS_SUCCESS: YES,
    }


def create_just_failure():
    return {
        FIELD_IS_SUCCESS: NOO,
    }


def create_unrecognized_error():
    return {
        **create_just_failure(),
        FIELD_ERROR_CODE: 0,
        FIELD_ERROR_MESSAGE: 'Unrecognized JSON error.',
    }


def create_only_json_allowed_error():
    return {
        **create_just_failure(),
        FIELD_ERROR_CODE: 1,
        FIELD_ERROR_MESSAGE: 'JSON requests is allowed only.',
    }


def create_wrong_json_error():
    return {
        **create_just_failure(),
        FIELD_ERROR_CODE: 2,
        FIELD_ERROR_MESSAGE: 'Wrong JSON request.',
    }


def create_validation_error(error_message):
    """Создаёт ошибку валидации данных."""
    return {
        **create_just_failure(),
        FIELD_ERROR_CODE: 4,
        FIELD_ERROR_MESSAGE: error_message,
    }


def create_parameters_is_not_enough_error():
    return {
        **create_just_failure(),
        FIELD_ERROR_CODE: 3,
        FIELD_ERROR_MESSAGE: 'Parameters is not enough to perform response. Did you forget something to send?',
    }


def create_player_already_exists_error():
    return {
        **create_just_failure(),
        FIELD_ERROR_CODE: 101,
        FIELD_ERROR_MESSAGE: 'The player already exists.',
    }


# Getters | Technical


def get_platform(struct):
    return str(struct.get(FIELD_PLATFORM, EMPTY))


def get_platform_id(struct):
    return str(struct.get(FIELD_PLATFORM_ID, EMPTY))


def get_platform_api_id(struct):
    return str(struct.get(FIELD_PLATFORM_API_ID, EMPTY))


def get_platform_auth_key(struct):
    return str(struct.get(FIELD_PLATFORM_AUTH_KEY, EMPTY))


def get_token(struct):
    return str(struct.get(FIELD_TOKEN, EMPTY))


def get_t(struct):

    try:
        t = int(struct.get(FIELD_T, 0))

    except (ValueError, TypeError) as _:
        t = 0

    return t


# Getters | Data fields


def get_fields_as_lists_or_nones(struct):
    """
    Извлекает поля из структуры как списки или None.
    
    Семантика:
    - None: поле отсутствует в запросе
    - []: поле присутствует, но пустое (для костюмов и таймеров означает "вернуть все")
    - [name1, name2, ...]: список запрошенных имён
    
    Возвращает кортеж (field_0, field_r, field_c, field_z).
    """
    field_names = (
        FIELD_0,
        FIELD_R,
        FIELD_C,
        FIELD_Z,
    )
    result = (None,) * len(field_names)

    if isinstance(struct, dict):
        result = tuple(
            tuple(map(str, struct[field_name])) if field_name in struct else None
            for field_name in field_names
        )

    return result


def get_fields_as_dictionaries_or_nones(struct):
    """
    Извлекает поля из структуры как словари или None.
    
    Семантика:
    - None: поле отсутствует в запросе
    - {}: поле присутствует, но пустое
    - {key: value, ...}: словарь с данными для обновления
    
    Преобразования значений:
    - FIELD_0: значения как есть
    - FIELD_R: целые числа >= 0 (количество ресурсов)
    - FIELD_C: булевы значения (True = добавить/оставить, False = удалить)
    - FIELD_Z: целые числа >= 0 (время таймеров, обычно игнорируется)
    
    Возвращает кортеж (field_0, field_r, field_c, field_z).
    """
    field_names_fns = {
        FIELD_0: lambda x: x,
        FIELD_R: lambda x: max(helpers.try_int(x), 0),
        FIELD_C: lambda x: bool(x),
        FIELD_Z: lambda x: max(helpers.try_int(x), 0),
    }
    result = (None,) * len(field_names_fns)

    if isinstance(struct, dict):

        def yield_field_fn_existence():
            for field_name, fn in field_names_fns.items():
                is_field_exists = field_name in struct
                field = struct[field_name] if is_field_exists else {}
                field = field if isinstance(field, dict) else {}
                yield field, fn, is_field_exists

        result = tuple(
            {str(k): fn(v) for k, v in field.items()} if is_field_exists else None
            for field, fn, is_field_exists in yield_field_fn_existence()
        )

    return result


# Getters | Common gameplay data


def _get_field_0_value(struct, field_name, field_type, default):
    try:
        d = struct.get(FIELD_0, {})
        value = field_type(d.get(field_name, default))
    except (AttributeError, ValueError, TypeError) as _:
        value = default
    return value


def get_player_id(struct):
    return _get_field_0_value(struct, PLAYER_ID, int, 0)


def get_level(struct):
    return _get_field_0_value(struct, PLAYER_LEVEL, int, 0)
