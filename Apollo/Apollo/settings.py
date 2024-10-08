from pathlib import Path
from mongoengine import connect
import os
from logging import Filter


__gpt_key_from_env = os.getenv('DB_NAME', None)
if __gpt_key_from_env: GPT_KEY = __gpt_key_from_env
else:
    with open("openai_key", "r") as f:
        GPT_KEY = f.read().strip()


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-3preg@l(5xp6wi64sa!yw=fmcfk&dj)lb6i6pmo_9r%(c6v_s9'


ON403REDIRECT = "/user/signin/"


DEBUG = True


ALLOWED_HOSTS = [
    "testserver",
    "127.0.0.1",
    "f50e-2603-7000-9600-680a-7d51-3778-ab37-320d.ngrok-free.app",
    "a49b-2603-7000-9600-6808-bd-d1b2-9f0b-5958.ngrok-free.app",
    "27e2-67-243-138-41.ngrok-free.app",
]


INSTALLED_APPS = [
    "rest_framework",
    "UserManager",
    "Conversation",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]


MIDDLEWARE = [
    "Apollo.middleware.RedirectOn403Middleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'Apollo.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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


WSGI_APPLICATION = 'Apollo.wsgi.application'


# MONGO_INSTANCE = connect(db='Apollo', host="mongodb://localhost:27017/")
MONGO_INSTANCE = connect(db='Apollo', host=os.getenv('MONGODB_CONNECTION_STRING'))


DATABASES = {
    
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': '3306',
    }
}


LANGUAGE_CODE = 'en-us'


TIME_ZONE = 'UTC'


USE_I18N = True


USE_TZ = True


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


USER_MANAGER_SETTINGS = {
    
    "TESTING_MODE": True,
    
    "EMAIL": {
        "SEND": False,
        "TEMPLATE": "Please click the following link to verify your account: {link}",
        "SUBJECT": "verify your email",
        "FROM": "luckyCasualGuy@gmail.com",
        "SMTP_USERNAME": "luckyCasualGuy@gmail.com",
        "SMTP_PASSWORD": "eojc yrxi bsjp ksql"
    },

    "ENABLE_COOKIES": True
    
}


class ThreadFilter(Filter):
    def filter(self, record):
        record.thread_id = record.thread  # Add thread ID to the log record
        return True


logs_foldir = BASE_DIR / 'logs'
logs_foldir.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {thread_id} {message}',
            'style': '{',
        },
    },
    'filters': {
        'thread_filter': { '()': ThreadFilter, },
    },
    'handlers': {
        'django_info_file': {
            'level': 'INFO',
            'filename': BASE_DIR / 'logs/django_info.log',

            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            
            # 'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            # 'maxBytes': 1024*1024*5,  # 5 MB
            
            'backupCount': 7,  # Keep the last 7 logs
            'formatter': 'verbose',
            'filters': ['thread_filter']
        },
        'converse_debug_file': {
            'level': 'DEBUG',
            'filename': BASE_DIR / 'logs/converse_debug.log',
            
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            
            # 'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            # 'maxBytes': 1024*1024*5,  # 5 MB
            
            'backupCount': 7,  # Keep the last 7 logs
            'formatter': 'verbose',
            'filters': ['thread_filter']
        },
        'converse_info_file': {
            'level': 'INFO',
            'filename': BASE_DIR / 'logs/converse_info.log',
            
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,

            # 'class': 'concurrent_log_handler.ConcurrentRotatingFileHandler',
            # 'maxBytes': 1024*1024*5,  # 5 MB
            
            'backupCount': 7,  # Keep the last 7 logs
            'formatter': 'verbose',
            'filters': ['thread_filter']
        },
    },
    'loggers': {
        'django': {
            'handlers': ['django_info_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'converse': {
            'handlers': ['converse_debug_file', 'converse_info_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'


STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]


STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')



"""
Added Athena health https://mydata.athenahealth.com/

client seecret: eyJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJodHRwczpcL1wvbXlkYXRhLmdlaGVhbHRoY2FyZS5jb20iLCJleHAiOjIwMzU5NzIzNDEsImlhdCI6MTcyMDQzOTU0MSwiaHR0cHM6XC9cL215ZGF0YS5nZWhlYWx0aGNhcmUuY29tXC9vYXV0aDIuY2xhaW1zXC9hcHBfaWQiOiJjZTE1NjMzNi1kY2Y0LTRlOWMtYTUyZC01YTJjZDEwMDRjOGEifQ.Zm8ZKDvQaXgaWSQoCdEzCqPs0yQrCf9u6RkrjcEfC09gDAZwLasKnoM3iJTE3PPcPnT7ijFBK0Px3S74r0OD-ZAj5UrfHqTEfUgwFCMjtoDx48_2l4tLJBzoEJnPynoH6rkdVJLpReD353dfrt08ZDBhaNbKwL8rGN2VbYGJ3oo
client id: eyJhbGciOiJSUzI1NiJ9.eyJjbGllbnRfdXJpIjoiaHR0cDpcL1wvbG9jYWxob3N0OjgwMDAiLCJncmFudF90eXBlcyI6WyJhdXRob3JpemF0aW9uX2NvZGUiXSwiaXNzIjoiaHR0cHM6XC9cL215ZGF0YS5nZWhlYWx0aGNhcmUuY29tIiwicmVkaXJlY3RfdXJpcyI6WyJodHRwczpcL1wvd3d3LnlvdXR1YmUuY29tXC8iXSwidG9rZW5fZW5kcG9pbnRfYXV0aF9tZXRob2QiOiJjbGllbnRfc2VjcmV0X2Jhc2ljIiwic29mdHdhcmVfaWQiOiIxIiwibmF0aXZlX2NsaWVudCI6ZmFsc2UsImh0dHBzOlwvXC9teWRhdGEuZ2VoZWFsdGhjYXJlLmNvbVwvb2F1dGgyLmNsYWltc1wvYXBwX2lkIjoiY2UxNTYzMzYtZGNmNC00ZTljLWE1MmQtNWEyY2QxMDA0YzhhIiwiZXhwIjoyMDM1OTcyMzQxLCJjbGllbnRfbmFtZSI6IkZTRCBIZWFsdGgiLCJpYXQiOjE3MjA0Mzk1NDEsImNvbnRhY3RzIjpbImx1Y2t5Q2FzdWFsR3V5QGdtYWlsLmNvbSJdLCJyZXNwb25zZV90eXBlcyI6WyJjb2RlIl19.OhiUaPufazMUGti0Oa92JkZ0zu77T5ICnGdDgsoNU0yfkaYMQ-ioZiF4VabBxhVYCh6RbyrGuNIV_u6771Y7TxXofNtHtdCMOA5fo9ZvDeCMV_yhxu7xgFouZu0A_vXy2aRYQHvie06H0dxzuedlNZIR9aJf2hcGThK6REancVc


https://ap23sandbox.fhirapi.athenahealth.com/demoAPIServer/oauth2/authorize?state=defaultState&scope=openid%20profile%20patient/*.read%20launch/patient&response_type=code&redirect_uri=https://www.youtube.com/&aud=https%3A%2F%2Fap22sandbox.fhirapi.athenahealth.com%2FdemoAPIServer&client_id=eyJhbGciOiJSUzI1NiJ9.eyJjbGllbnRfdXJpIjoiaHR0cDpcL1wvbG9jYWxob3N0OjgwMDAiLCJncmFudF90eXBlcyI6WyJhdXRob3JpemF0aW9uX2NvZGUiXSwiaXNzIjoiaHR0cHM6XC9cL215ZGF0YS5nZWhlYWx0aGNhcmUuY29tIiwicmVkaXJlY3RfdXJpcyI6WyJodHRwczpcL1wvd3d3LnlvdXR1YmUuY29tXC8iXSwidG9rZW5fZW5kcG9pbnRfYXV0aF9tZXRob2QiOiJjbGllbnRfc2VjcmV0X2Jhc2ljIiwic29mdHdhcmVfaWQiOiIxIiwibmF0aXZlX2NsaWVudCI6ZmFsc2UsImh0dHBzOlwvXC9teWRhdGEuZ2VoZWFsdGhjYXJlLmNvbVwvb2F1dGgyLmNsYWltc1wvYXBwX2lkIjoiY2UxNTYzMzYtZGNmNC00ZTljLWE1MmQtNWEyY2QxMDA0YzhhIiwiZXhwIjoyMDM1OTcyMzQxLCJjbGllbnRfbmFtZSI6IkZTRCBIZWFsdGgiLCJpYXQiOjE3MjA0Mzk1NDEsImNvbnRhY3RzIjpbImx1Y2t5Q2FzdWFsR3V5QGdtYWlsLmNvbSJdLCJyZXNwb25zZV90eXBlcyI6WyJjb2RlIl19.OhiUaPufazMUGti0Oa92JkZ0zu77T5ICnGdDgsoNU0yfkaYMQ-ioZiF4VabBxhVYCh6RbyrGuNIV_u6771Y7TxXofNtHtdCMOA5fo9ZvDeCMV_yhxu7xgFouZu0A_vXy2aRYQHvie06H0dxzuedlNZIR9aJf2hcGThK6REancVc
https://ap22sandbox.fhirapi.athenahealth.com/demoAPIServer/oauth2/authorize?state=defaultState&scope=openid%20profile%20patient/*.read%20launch/patient&response_type=code&redirect_uri=https://www.youtube.com/&aud=https%3A%2F%2Fap22sandbox.fhirapi.athenahealth.com%2FdemoAPIServer&client_id=eyJhbGciOiJSUzI1NiJ9.eyJjbGllbnRfdXJpIjoiaHR0cDpcL1wvbG9jYWxob3N0OjgwMDAiLCJncmFudF90eXBlcyI6WyJhdXRob3JpemF0aW9uX2NvZGUiXSwiaXNzIjoiaHR0cHM6XC9cL215ZGF0YS5nZWhlYWx0aGNhcmUuY29tIiwicmVkaXJlY3RfdXJpcyI6WyJodHRwczpcL1wvd3d3LnlvdXR1YmUuY29tXC8iXSwidG9rZW5fZW5kcG9pbnRfYXV0aF9tZXRob2QiOiJjbGllbnRfc2VjcmV0X2Jhc2ljIiwic29mdHdhcmVfaWQiOiIxIiwibmF0aXZlX2NsaWVudCI6ZmFsc2UsImh0dHBzOlwvXC9teWRhdGEuZ2VoZWFsdGhjYXJlLmNvbVwvb2F1dGgyLmNsYWltc1wvYXBwX2lkIjoiY2UxNTYzMzYtZGNmNC00ZTljLWE1MmQtNWEyY2QxMDA0YzhhIiwiZXhwIjoyMDM1OTcyMzQxLCJjbGllbnRfbmFtZSI6IkZTRCBIZWFsdGgiLCJpYXQiOjE3MjA0Mzk1NDEsImNvbnRhY3RzIjpbImx1Y2t5Q2FzdWFsR3V5QGdtYWlsLmNvbSJdLCJyZXNwb25zZV90eXBlcyI6WyJjb2RlIl19.OhiUaPufazMUGti0Oa92JkZ0zu77T5ICnGdDgsoNU0yfkaYMQ-ioZiF4VabBxhVYCh6RbyrGuNIV_u6771Y7TxXofNtHtdCMOA5fo9ZvDeCMV_yhxu7xgFouZu0A_vXy2aRYQHvie06H0dxzuedlNZIR9aJf2hcGThK6REancVc

"""

