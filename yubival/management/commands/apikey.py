from django.core.management.base import BaseCommand
from django.db import IntegrityError

from yubival.models import APIKey


class Command(BaseCommand):
    help = 'Manages API keys'
    requires_migrations_checks = True

    def _list(self):
        """Lists all API keys"""

        id_column_size = len(str(APIKey.objects.latest('id').id))
        row_format = '{:<%d} {:<}' % id_column_size

        for key in APIKey.objects.order_by('id'):
            self.stdout.write(row_format.format(key.id, key.label))

    def _add(self, label):
        """Adds an API key"""

        try:
            key = APIKey.objects.create(label=label)
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR('Failed creating key: %s' % e.args[0]))
            return

        self.stdout.write(self.style.SUCCESS('Created: id=%d, key=%s' % (key.id, key.key)))

    def _delete(self, key_id):
        """Deletes an API key"""

        try:
            key = APIKey.objects.get(id=key_id)
        except APIKey.DoesNotExist:
            self.stdout.write(self.style.ERROR('API key id=%d does not exist.' % int(key_id)))
            return

        key_str = str(key)
        key.delete()
        self.stdout.write(self.style.SUCCESS('Deleted: %s' % key_str))

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(
            title='subcommands',
            dest='subcommand',
            required=True,
        )

        parser_add = subparsers.add_parser('add', help='creates an API key')
        parser_add.add_argument('label', type=str, help='API key label')

        subparsers.add_parser('list', help='lists API keys')

        parser_delete = subparsers.add_parser('delete', help='deletes an API key')
        parser_delete.add_argument('id', type=int, help='deletes an API key')

    def handle(self, *args, **options):
        subcommand = options['subcommand']
        if subcommand == 'add':
            self._add(options['label'])
        elif subcommand == 'delete':
            self._delete(options['id'])
        else:  # subcommand == 'list'
            self._list()
