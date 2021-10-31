import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yubival', '0002_add_label_and_date_created_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='session_counter',
            field=models.IntegerField(default=0, editable=False, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(32767)]),
        ),
        migrations.AlterField(
            model_name='device',
            name='usage_counter',
            field=models.IntegerField(default=0, editable=False, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(255)]),
        ),
    ]
