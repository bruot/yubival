import base64

from django.db.models import Max
from django.test import TestCase

from django.contrib.auth import get_user_model
from django.http import QueryDict

from yubival.models import APIKey, Device
from yubival.views import hmac_verify_string, hmac_sign_string, is_request_signature_valid, \
    ordered_parameters_string, ordered_parameters, parse_response_line, parse_response, \
    response_signature


class TestHmacSignString(TestCase):
    def test_hmac_sign_string(self):
        # Example from https://developers.yubico.com/OTP/Specifications/Test_vectors.html

        # GIVEN
        key = base64.b64decode('mG5be6ZJU1qBGz24yPh/ESM3UdU=')
        text = 'id=1&nonce=jrFwbaYFhn0HoxZIsd9LQ6w2ceU&otp=vvungrrdhvtklknvrtvuvbbkeidikkvgglrvdgrfcdft'

        # WHEN
        signature = hmac_sign_string(text, key)

        # THEN
        self.assertEqual('+ja8S3IjbX593/LAgTBixwPNGX4=', signature)


class TestHmacVerifyString(TestCase):
    def test_valid_signature_is_valid(self):
        # Example from https://developers.yubico.com/OTP/Specifications/Test_vectors.html

        # GIVEN
        key = base64.b64decode('mG5be6ZJU1qBGz24yPh/ESM3UdU=')
        text = 'id=1&nonce=jrFwbaYFhn0HoxZIsd9LQ6w2ceU&otp=vvungrrdhvtklknvrtvuvbbkeidikkvgglrvdgrfcdft'
        signature = '+ja8S3IjbX593/LAgTBixwPNGX4='

        # WHEN
        is_valid = hmac_verify_string(text, signature, key)

        # THEN
        self.assertTrue(is_valid)

    def test_invalid_signature_is_invalid(self):
        # GIVEN
        key = base64.b64decode('mG5be6ZJU1qBGz24yPh/ESM3UdU=')
        text = 'ID=1&nonce=jrFwbaYFhn0HoxZIsd9LQ6w2ceU&otp=vvungrrdhvtklknvrtvuvbbkeidikkvgglrvdgrfcdft'
        signature = '+ja8S3IjbX593/LAgTBixwPNGX4='

        # WHEN
        is_valid = hmac_verify_string(text, signature, key)

        # THEN
        self.assertFalse(is_valid)

    def test_non_decodable_signature_is_invalid(self):
        # GIVEN
        key = base64.b64decode('mG5be6ZJU1qBGz24yPh/ESM3UdU=')
        text = 'id=1&nonce=jrFwbaYFhn0HoxZIsd9LQ6w2ceU&otp=vvungrrdhvtklknvrtvuvbbkeidikkvgglrvdgrfcdft'
        signature = '+ja8S3IjbX593/LAgTBixwPNGX4'

        # WHEN
        is_valid = hmac_verify_string(text, signature, key)

        # THEN
        self.assertFalse(is_valid)


class TestIsRequestSignatureValid(TestCase):
    def test_valid_signature_is_valid(self):
        # Example from https://developers.yubico.com/OTP/Specifications/Test_vectors.html

        # GIVEN
        key = base64.b64decode('mG5be6ZJU1qBGz24yPh/ESM3UdU=')
        q = QueryDict(
            'id=1&otp=vvungrrdhvtklknvrtvuvbbkeidikkvgglrvdgrfcdft&nonce=jrFwbaYFhn0HoxZIsd9LQ6w2ceU&h=%2Bja8S3IjbX593/LAgTBixwPNGX4%3D',
        )

        # WHEN
        is_valid = is_request_signature_valid(q, key)

        # THEN
        self.assertTrue(is_valid)

    def test_invalid_signature_is_valid(self):
        # GIVEN
        key = base64.b64decode('mG5be6ZJU1qBGz24yPh/ESM3UdU=')
        q = QueryDict(
            'id=2&otp=vvungrrdhvtklknvrtvuvbbkeidikkvgglrvdgrfcdft&nonce=jrFwbaYFhn0HoxZIsd9LQ6w2ceU&h=%2Bja8S3IjbX593/LAgTBixwPNGX4%3D',
        )

        # WHEN
        is_valid = is_request_signature_valid(q, key)

        # THEN
        self.assertFalse(is_valid)

    def test_no_signature_is_invalid(self):
        # GIVEN
        key = base64.b64decode('mG5be6ZJU1qBGz24yPh/ESM3UdU=')
        q = QueryDict(
            'id=1&otp=vvungrrdhvtklknvrtvuvbbkeidikkvgglrvdgrfcdft&nonce=jrFwbaYFhn0HoxZIsd9LQ6w2ceU',
        )

        # WHEN
        is_valid = is_request_signature_valid(q, key)

        # THEN
        self.assertFalse(is_valid)

    def test_multiple_values_for_key_is_invalid(self):
        # GIVEN
        key = base64.b64decode('deoe04KiDzdDIzMrq/xenLljbfQ=')
        q = QueryDict(
            'id=2&id=2&otp=vckhufhfnevgurllcliecctbktdrdnvcutbkgubghbfg&nonce=bef3a7835277a28da831005c2ae3b919e2076a62&h=r4ONAjl9oyIB3QTWnXWBwfPxin4%3D',
        )

        # WHEN
        is_valid = is_request_signature_valid(q, key)

        # THEN
        self.assertFalse(is_valid)


def get_status_from_response(response):
    lines = response.content.decode('utf-8').split('\r\n')
    for line in lines:
        if line.startswith('status='):
            return line[len('status='):]
    return None


class TestVerifyView(TestCase):
    def setUp(self):
        user_model = get_user_model()
        user_model.objects.create(username='foo')

        self.api_key = APIKey.objects.create(key=base64.b64encode(b'000000000001').decode('utf-8'))

        # Example at https://developers.yubico.com/OTP/Specifications/Test_vectors.html
        self.key = '000102030405060708090a0b0c0d0e0f'
        self.public_id = 'cdcdcdcdcdcd'
        self.private_id = '010203040506'
        Device.objects.create(
            public_id='cdcdcdcdcdcd',
            private_id=self.private_id,
            key=self.key,
            session_counter=0,
            usage_counter=0,
        )

    def test_valid_otp_gives_ok_status(self):
        # GIVEN
        # Example OTP at https://developers.yubico.com/OTP/Specifications/Test_vectors.html
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturecfllberrvkinnctnn',
            'nonce': 'fHUKs9',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertEqual('OK', get_status_from_response(response))

    def test_wrong_signature_gives_bad_signature_status(self):
        # GIVEN
        # Example OTP at https://developers.yubico.com/OTP/Specifications/Test_vectors.html
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturecfllberrvkinnctnn',
            'nonce': 'fHUKs9',
        })
        q['h'] = 'pOHpsdCn3f5pazYy4MK7P+Ol6zk='

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertEqual('BAD_SIGNATURE', get_status_from_response(response))

    def test_missing_nonce_gives_missing_parameter(self):
        # GIVEN
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturecfllberrvkinnctnn',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertEqual('MISSING_PARAMETER', get_status_from_response(response))

    def test_unknown_api_key_gives_no_such_client(self):
        # GIVEN
        unknown_api_key_id = APIKey.objects.aggregate(Max('id'))['id__max'] + 1
        q = QueryDict('', mutable=True)
        q.update({
            'id': unknown_api_key_id,
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturecfllberrvkinnctnn',
            'nonce': 'fHUKs9',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertEqual('NO_SUCH_CLIENT', get_status_from_response(response))

    def test_wrong_length_token_gives_bad_otp(self):
        # GIVEN
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturec',
            'nonce': 'fHUKs9',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertEqual('BAD_OTP', get_status_from_response(response))

    def test_unknown_device_gives_bad_otp(self):
        # GIVEN
        device = Device.objects.get(public_id=self.public_id)
        device.public_id = 'abcdcdcdcdcd'
        device.save()

        # Example OTP at https://developers.yubico.com/OTP/Specifications/Test_vectors.html
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturecfllberrvkinnctnn',  # has session and usage counters set to 1
            'nonce': 'fHUKs9',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertEqual('BAD_OTP', get_status_from_response(response))

    def test_ok_session_counter_bad_usage_counter_gives_replayed_otp_status(self):
        # GIVEN
        device = Device.objects.get(public_id=self.public_id)
        device.session_counter = 1
        device.usage_counter = 1
        device.save()

        # Example OTP at https://developers.yubico.com/OTP/Specifications/Test_vectors.html
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturecfllberrvkinnctnn',  # has session and usage counters set to 1
            'nonce': 'fHUKs9',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertEqual('REPLAYED_OTP', get_status_from_response(response))

    def test_ok_session_counter_same_usage_counter_gives_ok_status(self):
        # GIVEN
        device = Device.objects.get(public_id=self.public_id)
        device.session_counter = 0
        device.usage_counter = 1
        device.save()

        # Example OTP at https://developers.yubico.com/OTP/Specifications/Test_vectors.html
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturecfllberrvkinnctnn',  # has session and usage counters set to 1
            'nonce': 'fHUKs9',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertEqual('OK', get_status_from_response(response))

    def test_wrong_session_counter_gives_replayed_otp_status(self):
        # GIVEN
        device = Device.objects.get(public_id=self.public_id)
        device.session_counter = 2
        device.usage_counter = 0
        device.save()

        # Example OTP at https://developers.yubico.com/OTP/Specifications/Test_vectors.html
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturecfllberrvkinnctnn',  # has session and usage counters set to 1
            'nonce': 'fHUKs9',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertEqual('REPLAYED_OTP', get_status_from_response(response))

    def test_ok_usage_counter_same_session_counter_gives_ok_status(self):
        # GIVEN
        device = Device.objects.get(public_id=self.public_id)
        device.session_counter = 1
        device.usage_counter = 0
        device.save()

        # Example OTP at https://developers.yubico.com/OTP/Specifications/Test_vectors.html
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturecfllberrvkinnctnn',  # has session and usage counters set to 1
            'nonce': 'fHUKs9',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertEqual('OK', get_status_from_response(response))

    def test_wrong_aes_key_gives_bad_otp_status(self):
        # GIVEN

        device = Device.objects.get(public_id=self.public_id)
        device.key = '000102030405060708090a0b0c0d0e0a'
        device.save()

        # Example OTP at https://developers.yubico.com/OTP/Specifications/Test_vectors.html
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturecfllberrvkinnctnn',
            'nonce': 'fHUKs9',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertEqual('BAD_OTP', get_status_from_response(response))

    def test_wrong_private_id_gives_bad_otp_status(self):
        # GIVEN

        device = Device.objects.get(public_id=self.public_id)
        device.private_id = '010203040500'
        device.save()

        # Example OTP at https://developers.yubico.com/OTP/Specifications/Test_vectors.html
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturecfllberrvkinnctnn',
            'nonce': 'fHUKs9',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertEqual('BAD_OTP', get_status_from_response(response))

    def test_cr_lf_injection_in_nonce_hides_nonce(self):
        # GIVEN
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': 'cdcdcdcdcdcddvgtiblfkbgturecfllberrvkinnctnn',
            'nonce': '\r\nSTATUS=OK',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertNotContains(response, 'STATUS')

    def test_cr_lf_injection_in_otp_hides_otp(self):
        # GIVEN
        q = QueryDict('', mutable=True)
        q.update({
            'id': str(self.api_key.id),
            'otp': '\r\nSTATUS=OK\r\nxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',  # length 44 to facilitate OTP validation
            'nonce': 'fHUKs9',
        })
        q['h'] = hmac_sign_string(ordered_parameters_string(q, escape=True), base64.b64decode(self.api_key.key))

        # WHEN
        response = self.client.get('/wsapi/2.0/verify?%s' % q.urlencode())

        # THEN
        self.assertNotContains(response, 'STATUS')


class OrderedParametersTest(TestCase):
    def test_keys_order(self):
        # GIVEN
        params = {'b': 1, 'c': 2, 'aa': 3, 'a': 4}

        # WHEN
        ordered_params = ordered_parameters(params)

        # THEN
        self.assertEqual(['a', 'aa', 'b', 'c'], list(ordered_params.keys()))


class ParseResponseLineTest(TestCase):
    def test_common_line(self):
        # WHEN
        k, v = parse_response_line('alpha=beta')

        # THEN
        self.assertEqual('alpha', k)
        self.assertEqual('beta', v)

    def test_line_with_empty_key(self):
        # WHEN
        k, v = parse_response_line('=beta')

        # THEN
        self.assertEqual('', k)
        self.assertEqual('beta', v)

    def test_line_with_empty_value(self):
        # WHEN
        k, v = parse_response_line('alpha=')

        # THEN
        self.assertEqual('alpha', k)
        self.assertEqual('', v)


class ParseResponseTest(TestCase):
    def test_multiline_response(self):
        # GIVEN
        response = (
            "a=1\r\n"
            "bb=22\n"
            "cd=45\r\n"
        )

        # WHEN
        params = parse_response(response)

        # THEN
        self.assertEqual({'a': '1', 'bb': '22', 'cd': '45'}, params)


class ResponseSignatureTest(TestCase):
    def test_yubico_example(self):
        # Example at https://developers.yubico.com/OTP/Specifications/Test_vectors.html

        # GIVEN
        key = base64.b64decode('mG5be6ZJU1qBGz24yPh/ESM3UdU=')
        response = (
            "status=OK\r\n"
            "t=2019-06-06T05:14:15Z0369\r\n"
            "nonce=0123456789abcdef\r\n"
            "otp=cccccckdvvulethkhtvkrtbeukiettvfceekurncllcj\r\n"
            "sl=25\r\n"
        )

        # WHEN
        signature = response_signature(response, key)

        # THEN
        self.assertEqual('iCV9uFJDtuyELQsxFPnR80Yj2XU=', signature)
