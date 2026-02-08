ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.20
FROM ${BUILD_FROM}

WORKDIR /app

# Install build deps for native packages
RUN apk add --no-cache gcc musl-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY ui/ ./ui/

RUN mkdir -p /data

# s6-overlay service: run.sh is called by s6 as a long-running service
COPY run.sh /etc/services.d/work-schedule/run
RUN chmod a+x /etc/services.d/work-schedule/run
