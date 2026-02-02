import re
import hashlib
from uuid import uuid1
from datetime import datetime, timezone


_STAMP_MSEC_PRECISION = 1000.0
_STAMP_MSEC_PRECISION_INV = 1.0 / _STAMP_MSEC_PRECISION


def datetime_now_utc():
    return datetime.now(timezone.utc)


def default_random_string():
    return uuid1().hex


def get_request_referrer_domain(request):
    referrer = request.headers.get('Referer', '')  #@NOTE 'Referer' with single letter 'r'!
    match = re.match(r'(?:https?://)?([\w\d\-\.]+)(?::\d+)?(?:/\S*)?', referrer)
    domain = match.group(1) if match is not None else ''
    return domain


def datetime_to_stamp(dt):
    return int(dt.timestamp() * _STAMP_MSEC_PRECISION)


def stamp_to_datetime(s):
    return datetime.utcfromtimestamp(s * _STAMP_MSEC_PRECISION_INV)


def stringify(struct):
    """
    Преобразует структуру данных в строку для вычисления подписи.
    
    Важно: порядок элементов в списках и словарях не важен - они сортируются
    для обеспечения стабильности подписи независимо от порядка передачи.
    """
    def _(w):
        list_of_strings = []

        if isinstance(w, list):
            # Сортируем элементы списка для стабильности подписи
            list_of_strings.extend(['[', *(''.join(_(e)) for e in sorted(w, key=str)), ']'])

        elif isinstance(w, dict):
            # Сортируем ключи словаря для стабильности подписи
            list_of_strings.extend(f'{k}={"".join(_(w[k]))}' for k in sorted(w.keys(), key=str))

        else:
            list_of_strings.append(str(w))

        return list_of_strings

    return ''.join(_(struct))


def try_int(value, default=0, base=10):
    """
    Безопасно преобразует значение в целое число.
    
    Сначала пытается преобразовать как строку с указанным основанием,
    затем как обычное число. В случае ошибки возвращает значение по умолчанию.
    """
    if isinstance(value, int):
        return value
    
    try:
        result = int(value, base)  # Работает только если value - строка
    except (ValueError, TypeError):
        try:
            result = int(value)
        except (ValueError, TypeError):
            result = default
    return result


# vk.com specified functions

FIELD_NAME_VK_SIG = 'sig'
FIELD_NAME_VK_API_ID = 'api_id'
FIELD_NAME_VK_VIEWER_ID = 'viewer_id'
FIELD_NAME_VK_AUTH_KEY = 'auth_key'


def is_vk_urlvars_valid(vk_urlvars_as_dict, vk_app_secure_key):
    """Checks a signature of a query string that delivered from VK."""

    received_sig = vk_urlvars_as_dict.get(FIELD_NAME_VK_SIG, '')
    computed_sig = ''.join(
        f'{k}={vk_urlvars_as_dict[k]}'
        for k in sorted(vk_urlvars_as_dict.keys())
        if k != FIELD_NAME_VK_SIG
    )
    computed_sig = hashlib.md5(
        f'{computed_sig}{vk_app_secure_key}'.encode('utf-8')
    ).hexdigest()

    return computed_sig == received_sig


def is_vk_session_valid(vk_urlvars_as_dict, vk_app_secure_key):

    api_id = vk_urlvars_as_dict.get(FIELD_NAME_VK_API_ID, '')
    viewer_id = vk_urlvars_as_dict.get(FIELD_NAME_VK_VIEWER_ID, '')

    received_auth_key = vk_urlvars_as_dict.get(FIELD_NAME_VK_AUTH_KEY, '')
    computed_auth_key = hashlib.md5(
        f'{api_id}_{viewer_id}_{vk_app_secure_key}'.encode('utf-8')
    ).hexdigest()

    return received_auth_key == computed_auth_key
