FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt /app/

RUN apk --update --no-cache add gcc musl-dev libffi-dev openssl-dev postgresql-dev && \
    python -m venv .venv && \
    .venv/bin/pip install --upgrade pip && \
    .venv/bin/pip install -r requirements.txt && \
    apk del gcc musl-dev libffi-dev openssl-dev

COPY . /app/

RUN .venv/bin/python manage.py collectstatic --noinput

EXPOSE 8000

CMD .venv/bin/python manage.py makemigrations && \
    .venv/bin/python manage.py migrate && \
    .venv/bin/gunicorn platinum.wsgi:application --bind 0.0.0.0:8000 --workers 3 --log-level=info --access-logfile=/var/log/access.log --error-logfile=/var/log/error.log

