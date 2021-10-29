from django.test import TestCase

from yubival.models import generate_otp_key


class TestGenerateOtpKey(TestCase):
    def test_string_length(self):
        # WHEN
        key = generate_otp_key()

        # THEN
        self.assertEqual(32, len(key))
