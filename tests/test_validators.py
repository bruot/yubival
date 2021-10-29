from django.core.exceptions import ValidationError
from django.test import TestCase

from yubival.validators import validate_hex, validate_modhex, LengthValidator


class TestLengthValidator(TestCase):
    def test_matching_length_is_valid(self):
        # GIVEN
        validator = LengthValidator(4)
        value = 'abcd'

        # THEN
        try:
            validator(value)
        except ValidationError:
            self.fail('Value is invalid.')

    def test_nonmatching_length_is_invalid(self):
        # GIVEN
        validator = LengthValidator(4)
        value = 'abc'

        # THEN
        with self.assertRaises(ValidationError):
            validator(value)


class TestValidateHex(TestCase):
    def test_empty_is_valid(self):
        # GIVEN
        value = ''

        # THEN
        try:
            validate_hex(value)
        except ValidationError:
            self.fail('Value is invalid.')

    def test_hex_value_is_valid(self):
        # GIVEN
        value = '0123456789abcdfe'

        # THEN
        try:
            validate_hex(value)
        except ValidationError:
            self.fail('Value is invalid.')

    def test_nonhex_alphanumeric_character_is_invalid(self):
        # GIVEN
        value = 'g'

        # THEN
        with self.assertRaises(ValidationError):
            validate_hex(value)


class TestValidateModHex(TestCase):
    def test_empty_is_valid(self):
        # GIVEN
        value = ''

        # THEN
        try:
            validate_modhex(value)
        except ValidationError:
            self.fail('Value is invalid.')

    def test_modhex_value_is_valid(self):
        # GIVEN
        value = 'cbdefghijklnrtuv'

        # THEN
        try:
            validate_modhex(value)
        except ValidationError:
            self.fail('Value is invalid.')

    def test_nonhex_alphanumeric_character_is_invalid(self):
        # GIVEN
        value = '0'

        # THEN
        with self.assertRaises(ValidationError):
            validate_modhex(value)
