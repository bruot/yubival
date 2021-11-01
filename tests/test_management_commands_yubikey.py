from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.test.utils import captured_stderr

from yubival.models import Device


class CommandTest(TestCase):
    def test_successful_existing_device_addition(self):
        # GIVEN
        command = 'yubikey'
        args = ['add-existing', 'John', 'kkkkkkkkkkkk', '123456123456', '00112233445566778899aabbccddeeff']
        out = StringIO()

        # WHEN
        call_command(command, args, stdout=out)

        # THEN
        self.assertIn('Created: John (kkkkkkkkkkkk)', out.getvalue())
        device = Device.objects.get(public_id='kkkkkkkkkkkk')
        self.assertEqual('123456123456', device.private_id)
        self.assertEqual('00112233445566778899aabbccddeeff', device.key)

    def test_successful_device_addition(self):
        # GIVEN
        command = 'yubikey'
        args = ['add', 'John']
        out = StringIO()

        # WHEN
        call_command(command, args, stdout=out)

        # THEN
        self.assertIn('Created:', out.getvalue())
        self.assertIn('AES key:', out.getvalue())

    def test_missing_subcommand_parameter_raises_systemexit_and_shows_help(self):
        # GIVEN
        # `add` sub-argument is missing:
        command = 'yubikey'
        args = ['add-existing', 'John', 'kkkkkkkkkkkk', '123456123456']

        # THEN
        with captured_stderr() as err, self.assertRaises(SystemExit):
            call_command(command, args)
        self.assertIn('yubikey add-existing: error: the following arguments are required: key', err.getvalue())

    def test_already_existing_label_shows_error(self):
        # GIVEN
        command = 'yubikey'
        args = ['add', 'John']
        out = StringIO()

        # WHEN
        call_command(command, args)
        call_command(command, args, stdout=out)

        # THEN
        self.assertIn('Failed creating device: UNIQUE constraint failed: yubival_device.label', out.getvalue())

    def test_devices_listing(self):
        # GIVEN
        public_id_a = Device.objects.create(label='Yubikey A').public_id
        public_id_b = Device.objects.create(label='Yubikey B').public_id
        command = 'yubikey'
        args = ['list']
        out = StringIO()

        # WHEN
        call_command(command, args, stdout=out)
        output = out.getvalue()

        # THEN
        self.assertIn('%s Yubikey A' % public_id_a, output)
        self.assertIn('%s Yubikey B' % public_id_b, output)

    def test_deleting_existing_key_succeeds(self):
        # GIVEN
        public_id = Device.objects.create(label='John').public_id
        command = 'yubikey'
        args = ['delete', public_id]
        out = StringIO()

        # WHEN
        call_command(command, args, stdout=out)

        # THEN
        self.assertIn('Deleted: John (%s)' % public_id, out.getvalue())

    def test_deleting_nonexistent_key_shows_error(self):
        # GIVEN
        command = 'yubikey'
        args = ['delete', 'cccccccccccc']
        out = StringIO()

        # WHEN
        call_command(command, args, stdout=out)

        # THEN
        self.assertIn('Device public_id=cccccccccccc does not exist.', out.getvalue())
