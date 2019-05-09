"""
Django settings for privascope_portal project.

Generated by 'django-admin startproject' using Django 2.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import logging

import dj_database_url

# Add arbitrary settings from JSON-formatted key-value pairs
_locals = locals()
def _parse_env_vars_from_string(envs_string):
    import json
    env_dict = json.loads(envs_string)
    for k, v in env_dict.items():
        _locals[k] = v

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Logging

logger = logging.getLogger(__name__)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY_PORTAL')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'off').lower() in ('on', '1', 'yes')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1').split(',')

SITE_ID = 1

if os.getenv('ADMINS'):
    ADMINS = [tuple(l.split('=')) for l in os.getenv('ADMINS').split(",")]


# Application definition

INSTALLED_APPS = [
    'jobs',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'django_forms_bootstrap',
    'fsm_admin',
    'django_fsm_log',
]
try:
    __import__('django_extensions')
except ImportError:
    pass
else:
    INSTALLED_APPS += ('django_extensions',)

if os.getenv('ADDITIONAL_INSTALLED_APPS'):
    INSTALLED_APPS.append(os.getenv('ADDITIONAL_INSTALLED_APPS'))

if os.getenv('INSTALLED_APPS_ENV_VARS'):
    _parse_env_vars_from_string(os.getenv('INSTALLED_APPS_ENV_VARS'))

if os.getenv('RESTRICTED_ACCESS_GROUPS'):
    RESTRICTED_ACCESS_GROUPS = os.getenv('RESTRICTED_ACCESS_GROUPS').split(',')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
]

ROOT_URLCONF = 'privascope_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'privascope_portal.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(default='sqlite:///db.sqlite3/')
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Detroit'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Markdown
# https://github.com/trentm/python-markdown2/wiki/Extras

MARKDOWN_EXTRAS = [
    "break-on-newline",
    "fenced-code-blocks",
    "cuddled-lists"
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

PRIVATE_STORAGE_ROOT = os.getenv('PRIVATE_STORAGE_ROOT', '')

PRIVATE_JOB_OUTPUT_ROOT = os.path.join(BASE_DIR, os.getenv('PRIVATE_JOB_OUTPUT_ROOT', ''))

FILE_UPLOAD_HANDLERS = ['django.core.files.uploadhandler.TemporaryFileUploadHandler',]

# Arguments for configuring the resources available for a job container
# https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run

JOB_CONTAINER_MEM_LIMIT = os.getenv('JOB_CONTAINER_MEM_LIMIT')
JOB_CONTAINER_MEMSWAP_LIMIT = os.getenv('JOB_CONTAINER_MEMSWAP_LIMIT')
JOB_CONTAINER_CPU_PERIOD = int(os.getenv('JOB_CONTAINER_CPU_PERIOD')) if os.getenv('JOB_CONTAINER_CPU_PERIOD') else None
JOB_CONTAINER_CPU_QUOTA = int(os.getenv('JOB_CONTAINER_CPU_QUOTA')) if os.getenv('JOB_CONTAINER_CPU_QUOTA') else None
JOB_CONTAINER_VOLUME_MOUNT = os.getenv('JOB_CONTAINER_VOLUME_MOUNT', '/shared/')

# Environment variables to be passed into job run containers

JOB_ENV_FILE = os.getenv('JOB_ENV_FILE')
JOB_ENV_VARS = os.getenv('JOB_ENV_VARS')

if not (JOB_ENV_FILE or JOB_ENV_VARS):
    logger.warning('Neither JOB_ENV_FILE nor JOB_ENV_VARS are set!')
    job_envs_string = ''

if JOB_ENV_FILE:
    with open(JOB_ENV_FILE, 'r') as env_file:
        job_envs_string = env_file.read()

if JOB_ENV_VARS:
    job_envs_string = JOB_ENV_VARS

if JOB_ENV_FILE and JOB_ENV_VARS:
    logger.warning('Only one of JOB_ENV_FILE and JOB_ENV_VARS should be set. JOB_ENV_VARS will take precedence.')

job_envs_tuples = [tuple(l.split('=')) for l in job_envs_string.splitlines()]
JOB_ENV_DICT = { key: value for (key, value) in job_envs_tuples }


# Runner

RUNNER_QUEUE_USER = os.getenv('RUNNER_QUEUE_USER')
RUNNER_QUEUE_PASS = os.getenv('RUNNER_QUEUE_PASS')
CELERY_BROKER_URL = f'amqp://{RUNNER_QUEUE_USER}:{RUNNER_QUEUE_PASS}@rabbit:5672'


# Email

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', True)
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT = os.getenv('EMAIL_PORT', 587)
SERVER_EMAIL = os.getenv('SERVER_EMAIL')


# Site Configuration (needed for the URL in emails)

ABSOLUTE_URL_BASE = os.getenv('ABSOLUTE_URL_BASE')

# Where to go after login

LOGIN_REDIRECT_URL = '/'

LOGIN_URL = '/saml/login/'


#SAML Configuration

INSTALLED_APPS += ('djangosaml2',)
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'djangosaml2.backends.Saml2Backend',
)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

from os import path, getenv
import saml2
import tempfile
BASEDIR = path.dirname(path.abspath(__file__))

# Generate temp files for cert, key, and metadata
saml2_sp_cert = tempfile.NamedTemporaryFile('w+', buffering=1)
saml2_sp_cert.write(getenv('SAML2_SP_CERT') + '\n')

saml2_sp_key = tempfile.NamedTemporaryFile('w+', buffering=1)
saml2_sp_key.write(getenv('SAML2_SP_KEY') + '\n')

saml2_idp_metadata = tempfile.NamedTemporaryFile('w+', buffering=1)
saml2_idp_metadata.write(getenv('SAML2_IDP_METADATA') + '\n')

SAML_CONFIG = {
    'xmlsec_binary': '/usr/bin/xmlsec1',
    # 'entityid': '%smetadata/' % SAML2_URL_BASE,
    'entityid': getenv('SAML2_ENTITY_ID'), # e.g. https://yourdomain.cm/saml/metadata,

    # directory with attribute mapping
    # 'attribute_map_dir': path.join(BASEDIR, 'attribute-maps'),
    'name': getenv('SAML2_SP_NAME'),

    # this block states what services we provide
    'service': {
        'sp': {
            'name': getenv('SAML2_SP_NAME'),
            'name_id_format': ('urn:oasis:names:tc:SAML:2.0:'
                                'nameid-format:transient'),
            'authn_requests_signed': 'true',
            'allow_unsolicited': True,
            'endpoints': {
                # url and binding to the assetion consumer service view
                # do not change the binding or service name
                'assertion_consumer_service': [
                    (getenv('SAML2_ACS_POST'),
                    saml2.BINDING_HTTP_POST),
                ],
                # url and binding to the single logout service view+

                # do not change the binding or service name
                'single_logout_service': [
                    (getenv('SAML2_LS_REDIRECT'),
                    saml2.BINDING_HTTP_REDIRECT),
                    (getenv('SAML2_LS_POST'),
                    saml2.BINDING_HTTP_POST),
                ],
            },

            # attributes that this project needs to identify a user
            'required_attributes': getenv('SAML2_REQUIRED_ATTRIBUTES').split(','),

            # attributes that may be useful to have but not required
            'optional_attributes': getenv('SAML2_OPTIONAL_ATTRIBUTES').split(','),
        },
    },

    # where the remote metadata is stored
    'metadata': {
        'local': [saml2_idp_metadata.name],
    },

    # set to 1 to output debugging information
    'debug': 1 if DEBUG else 0,

    # certificate
    'key_file': saml2_sp_key.name,
    'cert_file': saml2_sp_cert.name,
}

SAML_CREATE_UNKNOWN_USER = True

SAML_ATTRIBUTE_MAPPING = {
    'uid': ('username', ),
    'mail': ('email', ),
    'givenName': ('first_name', ),
    'sn': ('last_name', ),
}
