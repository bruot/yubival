from io import StringIO
from django.core.management import call_command
from django.test import TestCase

from yubival.models import APIKey


class CommandTest(TestCase):
    def test_successful_key_addition(self):
        # GIVEN
        command = 'apikey'
        args = ['add', 'John']
        out = StringIO()

        # WHEN
        call_command(command, args, stdout=out)

        # THEN
        self.assertIn('Created: id=1, key=', out.getvalue())

    def test_already_existing_label_shows_error(self):
        # GIVEN
        command = 'apikey'
        args = ['add', 'John']
        out = StringIO()

        # WHEN
        call_command(command, args)
        call_command(command, args, stdout=out)

        # THEN
        self.assertIn('Failed creating key: UNIQUE constraint failed: yubival_apikey.label', out.getvalue())

    def test_key_listing(self):
        # GIVEN
        APIKey.objects.create(label='Key A')
        APIKey.objects.create(label='Key B')
        command = 'apikey'
        args = ['list']
        out = StringIO()

        # WHEN
        call_command(command, args, stdout=out)
        output = out.getvalue()

        # THEN
        self.assertIn('1 Key A', output)
        self.assertIn('2 Key B', output)

    def test_deleting_existing_key_succeeds(self):
        # GIVEN
        APIKey.objects.create(label='John')
        command = 'apikey'
        args = ['delete', '1']
        out = StringIO()

        # WHEN
        call_command(command, args, stdout=out)

        # THEN
        self.assertIn('Deleted: John (1)', out.getvalue())

    def test_deleting_nonexistent_key_shows_error(self):
        # GIVEN
        command = 'apikey'
        args = ['delete', '1']
        out = StringIO()

        # WHEN
        call_command(command, args, stdout=out)

        # THEN
        self.assertIn('API key id=1 does not exist.', out.getvalue())
