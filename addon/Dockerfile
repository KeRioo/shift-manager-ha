ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.20
FROM ${BUILD_FROM}

WORKDIR /app

# Install build deps for native packages
RUN apk add --no-cache gcc musl-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY ui/ ./ui/
COPY run.sh /

RUN chmod a+x /run.sh && mkdir -p /data

CMD ["/run.sh"]
