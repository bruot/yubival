from django.db import migrations, models
import django.utils.timezone


def set_apikey_labels(apps, schema_editor):
    APIKey = apps.get_model('yubival', 'APIKey')
    db_alias = schema_editor.connection.alias
    for api_key in APIKey.objects.using(db_alias).all():
        api_key.label = 'Label %d' % api_key.id
        api_key.save()


def set_device_labels(apps, schema_editor):
    Device = apps.get_model('yubival', 'Device')
    db_alias = schema_editor.connection.alias
    for device in Device.objects.using(db_alias).all():
        device.label = 'Label %d' % device.id
        device.save()


class Migration(migrations.Migration):

    dependencies = [
        ('yubival', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='apikey',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),

        migrations.AddField(
            model_name='apikey',
            name='label',
            field=models.CharField(max_length=64, null=True),
            preserve_default=False,
        ),
        migrations.RunPython(set_apikey_labels, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='apikey',
            name='label',
            field=models.CharField(max_length=64, unique=True, null=False),
            preserve_default=False,
        ),

        migrations.AddField(
            model_name='device',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),

        migrations.AddField(
            model_name='device',
            name='label',
            field=models.CharField(max_length=64, null=True),
            preserve_default=False,
        ),
        migrations.RunPython(set_device_labels, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='device',
            name='label',
            field=models.CharField(max_length=64, unique=True, null=False),
            preserve_default=False,
        ),
    ]
