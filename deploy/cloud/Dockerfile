FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-cloud.txt /tmp/requirements-cloud.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements-cloud.txt

COPY . /app

RUN mkdir -p /app/data/runtime /app/data/director_uploads /app/output

ENTRYPOINT ["/app/deploy/cloud/entrypoint.sh"]
