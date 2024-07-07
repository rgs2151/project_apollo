from pathlib import Path
from mongoengine import connect


with open("openai_key", "r") as f:
    GPT_KEY = f.read().strip()


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-3preg@l(5xp6wi64sa!yw=fmcfk&dj)lb6i6pmo_9r%(c6v_s9'


DEBUG = True


ALLOWED_HOSTS = [
    "testserver",
    "127.0.0.1"
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
    # 'django.contrib.staticfiles',
]


MIDDLEWARE = [
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
        'DIRS': ["templates"],
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


MONGO_INSTANCE = connect(db='Apollo', host="mongodb://localhost:27017/")


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'user_management',
        'USER': 'root',
        # 'PASSWORD': 'password',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}


LANGUAGE_CODE = 'en-us'


TIME_ZONE = 'UTC'


USE_I18N = True


USE_TZ = True


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


USER_MANAGER_SETTINGS = {
    
    "TESTING_MODE": False,
    
    "EMAIL": {
        "SEND": True,
        "TEMPLATE": "Please click the following link to verify your account: {link}",
        "SUBJECT": "verify your email",
        "FROM": "luckyCasualGuy@gmail.com",
        "SMTP_USERNAME": "luckyCasualGuy@gmail.com",
        "SMTP_PASSWORD": "eojc yrxi bsjp ksql"
    }
    
}

