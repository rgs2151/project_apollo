
FROM python:3.12.5-slim-bullseye

WORKDIR /app

COPY ./Apollo /app

COPY ./turbochat /app

COPY ./utility /app

RUN apt-get update && apt-get install -y \
    pkg-config \
    libmariadb-dev-compat \
    libmariadb-dev \
    build-essential

RUN pip install --no-cache-dir -r requirements.txt

# RUN mkdir -p /app/Apollo/logs

# CMD ["python"]

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=Apollo.settings

CMD ["python", "Apollo/manage.py", "runserver", "0.0.0.0:8000"]

