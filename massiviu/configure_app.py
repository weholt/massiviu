import os


def configure(appName):
    from django.conf import settings, global_settings
    _INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        appName,
    )

    the_module = __import__(appName)

    module_folder = os.path.split(the_module.__file__)[0]
    template_folder = os.path.join(module_folder, 'templates').replace(os.sep, '/')

    ROOT_URLCONF = appName + '.urls'

    settings.configure(default_settings=global_settings,
                       INSTALLED_APPS=_INSTALLED_APPS,
                       DATABASES={'default': {'NAME': ':memory:', 'ENGINE': 'django.db.backends.sqlite3'}},
                       ROOT_URLCONF=ROOT_URLCONF,
                       TEMPLATE_DIRS=(
                           template_folder
                       ),
                       SETTINGS_MODULE=appName
                       )

    from django.core.management import call_command
    import django
    django.setup()

    call_command('makemigrations', appName, interactive=False, verbosity=1)
    call_command('migrate', interactive=False, verbosity=1)
