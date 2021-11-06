![Default branch test status](https://github.com/bruot/yubival/actions/workflows/test.yml/badge.svg)
![main branch coverage](https://codecov.io/gh/bruot/yubival/branch/main/graph/badge.svg?token=PNVDEEOHTU)


# Yubival

This Django app runs a standalone Yubikey OTP validation server. It implements [version 2.0 of the validation protocol](https://developers.yubico.com/yubikey-val/Validation_Protocol_V2.0.html) limited to the case of a single validation server. YubiKey devices and server API keys can easily be managed in the Django admin site or via command line.


## Installation

Yubival can be integrated to any existing Django project. Alternatively, you can create a new Django site to host your validation server. If unfamiliar with Django, please follow the instructions at "Create a new standalone validation server" below.


### Add Yubival to an existing Django project

Install the package from PyPI:

```
$ pip install yubival
```

Add `'yubival'` to the `INSTALLED_APPS` setting in settings.py. It is not required to enable the admin site. If you do, `INSTALLED_APPS` may look like:

```
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'yubival',
]
```

Add the app URLs to the root urls.py file:

```
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # ...
    path('admin/', admin.site.urls),  # optional
    path('', include('yubival.urls')),
]
```

Update the database:

```
python manage.py migrate
```

When running the server, you should now be able to query the API at `/wsapi/2.0/verify`. When not providing any GET parameters, this returns a `MISSING_PARAMETER` status:

```
t=2021-10-29T08:31:11.885803
status=MISSING_PARAMETER
```


### Create a new standalone validation server

This section explains how to setup a new Django site with Yubival. It was tested on a Debian 10 distribution, with Python 3.9 and Django 3.2.

Create a directory for the project:

```
$ mkdir myyubival
$ cd myyubival
```

Create a Python environment and activate it:

```
$ python3 -m venv venv
$ source venv/bin/activate
```

Install Django and Yubival:

```
$ pip install Django yubival
```

Create a new Django project and browse to the newly created directory:

```
$ django-admin startproject myyubival
$ cd myyubival
```

Edit the _./myyubival/settings.py_ file to add `'yubival'` to the `INSTALLED_APPS` setting:

```
INSTALLED_APPS = [
    # ...
    'yubival',
]
```

Make the validation server URLs accessible by editing _./myyubival/urls.py_. Include the URLs from the Yubival app:

```
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='admin:index')),
    path('admin/', admin.site.urls),
    path('', include('yubival.urls')),
]
```

For convenience, we redirect above the website root to the admin area.

By default, Django will create a SQLite database located in a _db.sqlite3_ file in the project directory. To use other database engines, edit _./myyubival/settings.py_ to change the `DATABASES` setting; see the [Databases doc](https://docs.djangoproject.com/en/dev/ref/databases/). In both cases, run afterwards the following command to create the initial database tables:

```
python manage.py migrate
```

To be able to use the admin site and manage Yubikey devices and server API keys, create an initial user account:

```
$ python manage.py createsuperuser
```

To run the development web server, launch:

```
$ python manage.py runserver
```

The website can now be accessed at http://127.0.0.1:8000/. It should show a "Page not found" error. The validation API is located at http://127.0.0.1:8000/wsapi/2.0/verify and the admin site interface at http://127.0.0.1:8000/admin/.

While the `runserver` command above is an easy way to check your configuration and test Yubival, it should not be used to run the web server in production. Refer to the [deployment docs](https://docs.djangoproject.com/en/dev/howto/deployment/) to learn how to deploy your new myyubival site.


## Commands usage

### Getting help

All subcommands can print a detailed help with `--help`. Example:

```
$ python manage.py yubikey --help
$ python manage.py yubikey add-existing --help
```


### API keys management

Services that need to use the Yubival validation server require an API key which is a shared secret between Yubival and the service. The key is used to sign requests and responses to and from the validation server. API keys can be managed using the `manage.py apikey` command:

```
$ python manage.py apikey add service.example.com
Created: service.example.com (1):
    id: 1
    key: gnQ1sZWtRgCjm17waaiGHQptp8w=

$ python manage.py apikey list
1  service.example.com

$ python manage.py apikey delete 1
Deleted: service.example.com (1)
```


### Yubikey devices management

YubiKeys can be added, listed and deleted using the commands below. To add a key, either use `manage.py yubikey add` that will automatically generate a public ID, a private ID and an AES key that you can use to configure a new Yubikey device, or use `manage.py yubikey add-existing` if you have a YubiKey for which you already know its parameters, including its secret key. In any case, make sure that the Yubival server will be the only validation server for the YubiKeys you register. If not, it would become possible to reuse OTP.

```
$ python manage.py yubikey add James
Created: James (cnfbfdinbblh):
    Public ID: cnfbfdinbblh
    Private ID: 1b935e02e095
    AES key: fcea0ea12f97923ec4f952e0e170d419

$ python manage.py yubikey add-existing Evelyn gkhcilelifuv 0123456789ab 00112233445566778899aabbccddeeff
Created: Evelyn (gkhcilelifuv)

$ python manage.py yubikey list
cnfbfdinbblh James
gkhcilelifuv Evelyn

$ python manage.py yubikey delete cnfbfdinbblh
Deleted: James (cnfbfdinbblh)
```
