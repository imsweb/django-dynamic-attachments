import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Make sure the copy of attachments in the directory above this one is used.
sys.path.insert(0, BASE_DIR)

SECRET_KEY = 'attachment_tests_secret'

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'attachments',
    'core',
    'django_coverage',
)

ROOT_URLCONF = 'urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
)

TEST_RUNNER = 'teamcity.django.TeamcityDjangoRunner'

COVERAGE_REPORT_HTML_OUTPUT_DIR = os.path.join(BASE_DIR, 'coverage_html')
COVERAGE_MODULE_EXCLUDES = ('tests$', 'urls$', 'admin$', 'django', 'migrations', 'management', 'pipeline')
