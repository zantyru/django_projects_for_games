import json
import hashlib
from .. import helpers


YES = 1
NOO = 0
EMPTY = ''

# Names of sections
FIELD_0 = '0'  # Common gameplay data for player
FIELD_R = 'r'  # Player's resources
FIELD_C = 'c'  # Player's costumes
FIELD_Z = 'z'  # Player's timers

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

    try:
        data = json.loads(json_object)

    except json.JSONDecodeError:
        data = {}

    return data


def signify(struct, secret):

    if not isinstance(struct, dict):
        raise ValueError("First parameter must be a dictionary.")

    struct[FIELD_SIGNATURE] = hashlib.md5(
        f'{helpers.stringify(struct)}{secret}'.encode('utf-8')
    ).hexdigest()


def is_successful(struct):
    return struct.get(FIELD_IS_SUCCESS, NOO) == YES


def is_signed_well(struct, secret):

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
