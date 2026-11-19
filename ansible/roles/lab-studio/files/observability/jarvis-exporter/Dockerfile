FROM python:3.12.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --require-hashes -r requirements.txt

COPY jarvis_exporter ./jarvis_exporter
COPY tests ./tests
RUN python -m unittest discover -s tests -v && rm -rf tests

RUN addgroup --system --gid 10001 jarvis \
    && adduser --system --uid 10001 --ingroup jarvis --no-create-home jarvis

USER 10001:10001

EXPOSE 9102

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9102/healthz', timeout=3).read()"]

ENTRYPOINT ["python", "-m", "jarvis_exporter"]

