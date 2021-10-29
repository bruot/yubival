import django.core.validators
from django.db import migrations, models
import yubival.models
import yubival.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='APIKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(default=yubival.models.generate_api_key, max_length=28, validators=[yubival.validators.LengthValidator(28)])),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.CharField(default=yubival.models.generate_public_id, max_length=12, unique=True, validators=[yubival.validators.LengthValidator(12), yubival.validators.validate_modhex])),
                ('private_id', models.CharField(default=yubival.models.generate_private_id, max_length=12, unique=True, validators=[yubival.validators.LengthValidator(12), yubival.validators.validate_hex])),
                ('key', models.CharField(default=yubival.models.generate_otp_key, max_length=32, validators=[yubival.validators.LengthValidator(32), yubival.validators.validate_hex])),
                ('session_counter', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(32767)])),
                ('usage_counter', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(255)])),
            ],
        ),
    ]
