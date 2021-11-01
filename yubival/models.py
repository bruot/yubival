import base64
import secrets

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from yubiotp.modhex import modhex

from yubival.validators import validate_modhex, validate_hex, LengthValidator


API_KEY_BYTE_LENGTH = 20
DEVICE_PUBLIC_ID_BYTE_LENGTH = 6
DEVICE_PRIVATE_ID_BYTE_LENGTH = 6
DEVICE_KEY_BYTE_LENGTH = 16


def generate_api_key():
    return base64.b64encode(secrets.token_bytes(API_KEY_BYTE_LENGTH)).decode('utf-8')


def generate_otp_key():
    return secrets.token_hex(16)


def generate_public_id():
    return modhex(secrets.token_bytes(DEVICE_PRIVATE_ID_BYTE_LENGTH)).decode('utf-8')


def generate_private_id():
    return secrets.token_hex(DEVICE_PRIVATE_ID_BYTE_LENGTH)


class APIKey(models.Model):
    label = models.CharField(
        max_length=64,
        unique=True,
    )
    key = models.CharField(
        max_length=4 * ((API_KEY_BYTE_LENGTH + 2) // 3),  # Max length after base64 conversion
        validators=[LengthValidator(4 * ((API_KEY_BYTE_LENGTH + 2) // 3))],
        default=generate_api_key,
    )
    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return '%s (%d)' % (self.label, self.id)


class Device(models.Model):
    label = models.CharField(
        max_length=64,
        unique=True,
    )
    public_id = models.CharField(
        unique=True, max_length=2 * DEVICE_PUBLIC_ID_BYTE_LENGTH,
        validators=[LengthValidator(2 * DEVICE_PUBLIC_ID_BYTE_LENGTH), validate_modhex],
        default=generate_public_id,
    )
    private_id = models.CharField(
        unique=True, max_length=2 * DEVICE_PRIVATE_ID_BYTE_LENGTH,
        validators=[LengthValidator(2 * DEVICE_PRIVATE_ID_BYTE_LENGTH), validate_hex],
        default=generate_private_id,
    )
    key = models.CharField(
        max_length=2 * DEVICE_KEY_BYTE_LENGTH,
        validators=[LengthValidator(2 * DEVICE_KEY_BYTE_LENGTH), validate_hex],
        default=generate_otp_key,
    )
    session_counter = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(2**15 - 1)],
        default=0,
        editable=False,
    )
    usage_counter = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(255)],
        default=0,
        editable=False,
    )
    date_created = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return '%s (%s)' % (self.label, self.public_id)
