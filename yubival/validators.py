import string

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


def argparse_type(field, func_name=None):
    """Creates an argparse type corresponding to a Django model field

    Returns a function that can be used as an argparse parameter type that performs input validation and conversion
    that correspond to a given Django model field.

    Args:
        field: a Django database model field class such as IntegerField.
        func_name: name of the type function that may be shown in argparse parsing error messages.

    Returns:
        type_func: function that converts its input value to a value with a data type consistent with the field provided
            above. If there are validation errors, a `ValueError` is raised.
    """

    def type_func(value):
        value = field.get_prep_value(value)

        for v in field.validators:
            try:
                v(value)
            except ValidationError:
                raise ValueError

        return value

    if func_name is not None:
        type_func.__name__ = func_name

    return type_func


@deconstructible
class LengthValidator:
    def __init__(self, length):
        self.length = length

    def __call__(self, value):
        if len(value) != self.length:
            raise ValidationError("Must be of length %d." % self.length)


def validate_hex(value):
    if not all(c in string.hexdigits for c in value):
        raise ValidationError("Must be composed of hexadecimal characters.")


def validate_modhex(value):
    if not all(c in 'cbdefghijklnrtuv' for c in value):
        raise ValidationError("Must be composed of modhex characters.")
