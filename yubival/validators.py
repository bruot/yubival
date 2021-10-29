import string

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


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
