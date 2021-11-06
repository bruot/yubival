import random

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from yubiotp.modhex import modhex

from yubival.models import Device, DEVICE_PUBLIC_ID_BYTE_LENGTH, DEVICE_PRIVATE_ID_BYTE_LENGTH
from yubival.validators import argparse_type


class Command(BaseCommand):
    help = 'Manages YubiKey devices'
    requires_migrations_checks = True

    def _list(self):
        """Lists all registered YubiKeys"""

        row_format = '{:%d} {:<}' % DEVICE_PUBLIC_ID_BYTE_LENGTH

        for key in Device.objects.order_by('id'):
            self.stdout.write(row_format.format(key.public_id, key.label))

    def _add(self, label):
        """Registers a YubiKey by autogenerating device IDs and key"""
        try:
            device = Device.objects.create(label=label)
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR('Failed creating device: %s' % e.args[0]))
            return

        self.stdout.write(self.style.SUCCESS('Created: %s:' % str(device)))
        self.stdout.write('\tPublic ID: %s' % device.public_id)
        self.stdout.write('\tPrivate ID: %s' % device.private_id)
        self.stdout.write('\tAES key: %s' % device.key)

    def _add_existing(self, label, public_id, private_id, key):
        """Registers an existing YubiKey"""
        try:
            device = Device.objects.create(
                label=label,
                public_id=public_id,
                private_id=private_id,
                key=key,
            )
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR('Failed creating device: %s' % e.args[0]))
            return

        self.stdout.write(self.style.SUCCESS('Created: %s' % str(device)))

    def _delete(self, public_id):
        """Deletes a YubiKey"""
        try:
            device = Device.objects.get(public_id=public_id)
        except Device.DoesNotExist:
            self.stdout.write(self.style.ERROR('Device public_id=%s does not exist.' % public_id))
            return

        device_str = str(device)
        device.delete()
        self.stdout.write(self.style.SUCCESS('Deleted: %s' % device_str))

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(
            title='subcommands',
            dest='subcommand',
        )
        subparsers.required = True

        parser_add = subparsers.add_parser(
            'add',
            called_from_command_line=True,
            description='Registers a YubiKey with random IDs and secret key that can be uploaded to a YubiKey',
        )
        parser_add.add_argument('label', type=str, help='device label')

        parser_add_existing = subparsers.add_parser(
            'add-existing',
            called_from_command_line=True,
            description='Registers an already configured YubiKey',
        )

        random.seed(314159)
        example_public_id = modhex(bytearray([
            random.getrandbits(8) for _ in range(DEVICE_PUBLIC_ID_BYTE_LENGTH)
        ])).decode('utf-8')
        example_private_id = bytearray([
            random.getrandbits(8) for _ in range(DEVICE_PRIVATE_ID_BYTE_LENGTH)
        ]).hex()

        parser_add_existing.add_argument(
            'label',
            type=argparse_type(Device._meta.get_field('label')),
            help='device label',
        )
        parser_add_existing.add_argument(
            'public_id',
            type=argparse_type(Device._meta.get_field('public_id'), 'public_id_type'),
            help='public ID (%d-byte modhex such as "%s")' % (DEVICE_PUBLIC_ID_BYTE_LENGTH, example_public_id),
        )
        parser_add_existing.add_argument(
            'private_id',
            type=argparse_type(Device._meta.get_field('private_id'), 'private_id_type'),
            help='private ID (%d-byte hexadecimal such as "%s")' % (DEVICE_PRIVATE_ID_BYTE_LENGTH, example_private_id),
        )
        parser_add_existing.add_argument(
            'key',
            type=argparse_type(Device._meta.get_field('key'), 'key_type'),
            help='AES key (16-byte hexadecimal such as "00112233445566778899aabbccddeeff")',
        )

        subparsers.add_parser(
            'list',
            called_from_command_line=True,
            description='Lists YubiKeys',
        )

        parser_delete = subparsers.add_parser(
            'delete',
            called_from_command_line=True,
            description='Deletes a YubiKey',
        )
        parser_delete.add_argument(
            'public_id',
            type=str,
            help='YubiKey public ID (%d-byte modhex such as "%s")' % (DEVICE_PUBLIC_ID_BYTE_LENGTH, example_public_id),
        )

    def handle(self, *args, **options):
        subcommand = options['subcommand']
        if subcommand == 'add':
            self._add(options['label'])
        elif subcommand == 'add-existing':
            self._add_existing(options['label'], options['public_id'], options['private_id'], options['key'])
        elif subcommand == 'delete':
            self._delete(options['public_id'])
        else:  # subcommand == 'list'
            self._list()
