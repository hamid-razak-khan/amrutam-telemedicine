import os
from pathlib import Path
from datetime import timedelta
import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / '.env')
load_dotenv()

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'amrutam-telemedicine-dev-insecure-secret-key-32charslong!')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,testserver').split(',')]
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
]

LOCAL_APPS = [
    'apps.common.apps.CommonConfig',
    'apps.accounts.apps.AccountsConfig',
    'apps.doctors.apps.DoctorsConfig',
    'apps.availability.apps.AvailabilityConfig',
    'apps.bookings.apps.BookingsConfig',
    'apps.consultations.apps.ConsultationsConfig',
    'apps.prescriptions.apps.PrescriptionsConfig',
    'apps.payments.apps.PaymentsConfig',
    'apps.audit.apps.AuditConfig',
    'apps.analytics.apps.AnalyticsConfig',
]

INSTALLED_APPS = ['django_prometheus'] + DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'apps.common.middleware.RequestIdMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.audit.middleware.AuditLoggingMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Database Configuration
# Supabase PostgreSQL configuration with SSL and automatic IPv6 -> Session Pooler fallback support
db_engine_override = os.getenv('DB_ENGINE', 'postgres').lower()
database_url = os.getenv('DATABASE_URL')
db_host = os.getenv('DB_HOST', '')
use_db_pooler = os.getenv('USE_DB_POOLER', 'False').lower() in ('true', '1', 'yes')

if db_engine_override == 'sqlite' and not (db_host and db_engine_override in ('postgres', 'postgresql')):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 30,  # 30-second lock timeout for concurrency testing
            }
        }
    }
elif database_url:
    DATABASES = {
        'default': dj_database_url.parse(
            database_url,
            conn_max_age=int(os.getenv('DB_CONN_MAX_AGE', '600')),
            ssl_require=True
        )
    }
    DATABASES['default'].setdefault('OPTIONS', {})['sslmode'] = os.getenv('DB_SSLMODE', 'require')
else:
    # Direct vs Supabase Session Pooler connection resolution
    # Direct Supabase endpoints (db.<ref>.supabase.co:5432) resolve to IPv6 only.
    # If IPv6 routing is unavailable or USE_DB_POOLER=True, route to Supabase Session Pooler (port 5432).
    pooler_host = os.getenv('DB_POOLER_HOST', 'aws-0-ap-northeast-2.pooler.supabase.com')
    pooler_port = os.getenv('DB_POOLER_PORT', '5432')  # Session pooler port
    pooler_user = os.getenv('DB_POOLER_USER', 'postgres.hsmnnakttfzddyzixdkm')

    if use_db_pooler:
        active_host = pooler_host
        active_port = pooler_port
        active_user = pooler_user
    else:
        active_host = db_host or 'db.hsmnnakttfzddyzixdkm.supabase.co'
        active_port = os.getenv('DB_PORT', '5432')
        active_user = os.getenv('DB_USER', 'postgres')


    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'postgres'),
            'USER': active_user,
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': active_host,
            'PORT': active_port,
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '600')),
            'OPTIONS': {
                'sslmode': os.getenv('DB_SSLMODE', 'require'),
                'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '10')),
            }
        }
    }


from django.db.backends.signals import connection_created

def configure_sqlite_concurrency(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        try:
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA journal_mode=WAL;')
                cursor.execute('PRAGMA busy_timeout=10000;')
        except Exception:
            pass

connection_created.connect(configure_sqlite_concurrency)

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.getenv('ANON_THROTTLE_RATE', '120/min'),
        'user': os.getenv('USER_THROTTLE_RATE', '600/min'),
    }
}

# SimpleJWT Configuration
JWT_ACCESS_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', '15'))
JWT_REFRESH_DAYS = int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME_DAYS', '7'))

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=JWT_ACCESS_MINUTES),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=JWT_REFRESH_DAYS),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Multi-Factor Authentication (MFA) Configuration
MFA_ENCRYPTION_KEY = os.getenv('MFA_ENCRYPTION_KEY')
MFA_ISSUER_NAME = os.getenv('MFA_ISSUER_NAME', 'Amrutam Telemedicine')
MFA_CHALLENGE_TIMEOUT_MINUTES = int(os.getenv('MFA_CHALLENGE_TIMEOUT_MINUTES', '5'))


# drf-spectacular OpenAPI 3.0 Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Amrutam Telemedicine Platform API',
    'DESCRIPTION': 'Enterprise Telemedicine REST API featuring strict RBAC, transactional booking with pessimistic locking, idempotency protection, consultation workflows, and operational metrics.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/v1',
    'COMPONENT_SPLIT_REQUEST': True,
}

# CORS Configuration
cors_origins_raw = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins_raw.split(',') if origin.strip()]
if DEBUG:
    # Allow all localhost and 127.0.0.1 ports during local development
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^http://localhost:\d+$",
        r"^http://127\.0\.0\.1:\d+$",
    ]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'idempotency-key',
    'x-request-id',
]

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'True').lower() in ('true', '1', 't')

# Observability & Metrics
METRICS_TOKEN = os.getenv('METRICS_TOKEN', 'internal-metrics-secret-key-amrutam')

# Structured JSON Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'apps.common.logging.JSONFormatter',
        },
        'simple': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json' if not DEBUG else 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'amrutam': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Production Security Headers
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
