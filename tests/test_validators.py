from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db.models import FloatField, IntegerField
from django.test import TestCase

from yubival.validators import validate_hex, validate_modhex, LengthValidator, argparse_type


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


class TestArgparseType(TestCase):
    def test_function_returns_ouptput_data_type(self):
        # GIVEN
        field = FloatField()
        type_func = argparse_type(field)

        # WHEN
        new_value = type_func('123')

        # THEN
        self.assertTrue(type(new_value) is float)

    def test_function_returns_value(self):
        # GIVEN
        field = FloatField()
        type_func = argparse_type(field)

        # WHEN
        new_value = type_func('123')

        # THEN
        self.assertEqual(123.0, new_value)

    def test_function_has_custom_name(self):
        # GIVEN
        field = FloatField()

        # WHEN
        type_func = argparse_type(field, 'custom')

        # THEN
        self.assertEqual('custom', type_func.__name__)

    def test_nonconvertible_input_raises_exception(self):
        # GIVEN
        field = IntegerField()
        type_func = argparse_type(field)

        # THEN
        with self.assertRaises(ValueError):
            type_func('abc')

    def test_function_raises_valueerror_when_validator_fails(self):
        # GIVEN
        field = IntegerField(validators=[MaxValueValidator(10)])
        type_func = argparse_type(field)

        # THEN
        with self.assertRaises(ValueError):
            type_func(20)
