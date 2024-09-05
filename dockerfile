
FROM python:3.10.14-alpine3.20

WORKDIR /app

COPY ./Apollo /app

COPY ./turbochat /app

COPY ./utility /app

RUN apk add --no-cache mariadb-connector-c-dev build-base

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=Apollo.settings

CMD ["python", "Apollo/manage.py", "runserver", "0.0.0.0:8000"]

