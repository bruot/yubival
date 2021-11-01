import base64
import datetime
import hashlib
import hmac
from binascii import hexlify
from collections import OrderedDict
from enum import Enum

from django.db import transaction
from django.http import HttpResponse
from django.utils.http import urlencode
from django.views import View
from yubiotp.otp import decode_otp

from yubival.models import APIKey, Device


class ValidationStatus(Enum):
    OK = 'OK'
    BAD_OTP = 'BAD_OTP'
    REPLAYED_OTP = 'REPLAYED_OTP'
    BAD_SIGNATURE = 'BAD_SIGNATURE'
    MISSING_PARAMETER = 'MISSING_PARAMETER'
    NO_SUCH_CLIENT = 'NO_SUCH_CLIENT'
    OPERATION_NOT_ALLOWED = 'OPERATION_NOT_ALLOWED'
    BACKEND_ERROR = 'BACKEND_ERROR'
    NOT_ENOUGH_ANSWERS = 'NOT_ENOUGH_ANSWERS'
    REPLAYED_REQUEST = 'REPLAYED_REQUEST'


def ordered_parameters(params):
    ordered_params = OrderedDict()
    for key in sorted(params):
        ordered_params[key] = params[key]
    return ordered_params


def parse_response_line(line):
    k = line.find('=')
    key = line[:k]
    value = line[k + 1:]
    return key, value


def parse_response(text):
    params = {}
    for line in text.split('\n'):
        line = line.strip()
        if line != '':
            key, value = parse_response_line(line)
            params[key] = value
    return params


def response_signature(text, api_key):
    ordered_params = ordered_parameters(parse_response(text))
    # In opposition to request URls, the date here should not be escaped.
    text = '&'.join('%s=%s' % (k, v) for k, v in ordered_params.items())
    return hmac_sign_string(text, api_key)


def response_parameters_to_text(response_params):
    return ''.join(
        '%s=%s\r\n' % (k, v) for k, v in response_params.items()
    )


def http_text_response(response_params):
    return HttpResponse(response_parameters_to_text(response_params), content_type='text/plain')


def signed_http_text_response(response_params, api_key):
    text = response_parameters_to_text(response_params)
    signature = response_signature(text, api_key)
    text = 'h=%s\r\n%s' % (signature, text)
    return HttpResponse(text, content_type='text/plain')


def get_api_key_or_none(str_id):
    try:
        key_id = int(str_id)
    except ValueError:
        return

    try:
        return APIKey.objects.get(id=key_id)
    except APIKey.DoesNotExist:
        return


def hmac_sign_string(text, key):
    hashed = hmac.new(key, text.encode('utf-8'), hashlib.sha1)
    return base64.encodebytes(hashed.digest()).decode('utf-8')[:-1]


def ordered_parameters_string(query_dict, escape):
    sorted_keys = sorted(query_dict.keys())
    params = []
    for key in sorted_keys:
        for value in sorted(query_dict.getlist(key)):
            params.append((key, value))

    ordered_params = OrderedDict(params)
    if escape:
        return urlencode(ordered_params)
    else:
        return '&'.join('%s=%s' % (k, v) for k, v in ordered_params.items())


def hmac_verify_string(text, signature, key):
    expected_signature = hmac_sign_string(text, key)
    return hmac.compare_digest(signature, expected_signature)


def is_request_signature_valid(query_dict, api_key):
    # Reject if any key appears more than once
    if any(len(l) > 1 for _, l in query_dict.lists()):
        return False

    q = query_dict.copy()

    try:
        signatures = q.pop('h')
    except KeyError:
        return False
    signature = signatures[0]

    text = ordered_parameters_string(q, escape=True)
    return hmac_verify_string(text, signature, api_key)


class VerifyView(View):
    def get(self, request, *args, **kwargs):
        response = {
            't': datetime.datetime.utcnow().isoformat(),
        }

        required_fields = ['id', 'otp', 'nonce']
        if not all(name in request.GET for name in required_fields):
            response['status'] = ValidationStatus.MISSING_PARAMETER.value
            return http_text_response(response)

        token = request.GET.getlist('otp')[0]

        nonce = request.GET.getlist('nonce')[0]
        if '\r' in nonce or '\n' in nonce:
            response['status'] = ValidationStatus.MISSING_PARAMETER.value
            return http_text_response(response)

        response['nonce'] = nonce

        api_key = get_api_key_or_none(request.GET['id'])
        if api_key is None:
            response['status'] = ValidationStatus.NO_SUCH_CLIENT.value
            return http_text_response(response)

        key = base64.b64decode(api_key.key)

        if not is_request_signature_valid(request.GET, key):
            response['status'] = ValidationStatus.BAD_SIGNATURE.value
            return signed_http_text_response(response, key)

        if len(token) != 44 or '\r' in token or '\n' in token:
            response['status'] = ValidationStatus.BAD_OTP.value
            return signed_http_text_response(response, key)

        response['otp'] = token

        public_id = token[:12]
        devices = Device.objects.select_for_update().filter(public_id=public_id)
        with transaction.atomic():
            try:
                device = devices.get()
            except Device.DoesNotExist:
                response['status'] = ValidationStatus.BAD_OTP.value
                return signed_http_text_response(response, key)

            try:
                _, otp = decode_otp(token.encode('utf-8'), bytes.fromhex(device.key))
            except Exception:
                response['status'] = ValidationStatus.BAD_OTP.value
                return signed_http_text_response(response, key)

            response['sessionuse'] = otp.session
            response['sessioncounter'] = otp.counter
            response['timestamp'] = otp.timestamp

            if hexlify(otp.uid) != device.private_id.encode('utf-8'):
                response['status'] = ValidationStatus.BAD_OTP.value
                return signed_http_text_response(response, key)

            if otp.session < device.session_counter:
                response['status'] = ValidationStatus.REPLAYED_OTP.value
                return signed_http_text_response(response, key)

            if (otp.session == device.session_counter) and (otp.counter <= device.usage_counter):
                response['status'] = ValidationStatus.REPLAYED_OTP.value
                return signed_http_text_response(response, key)

            # OTP is valid; we update the counters:
            device.session_counter = otp.session
            device.usage_counter = otp.counter
            device.save()

        response['status'] = ValidationStatus.OK.value
        response['sl'] = 1
        return signed_http_text_response(response, key)
