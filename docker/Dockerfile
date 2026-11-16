FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid 10001 socbot \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin socbot

WORKDIR /app

COPY --chown=root:root wazuh/firewall/firewall.py /app/firewall.py
COPY --chown=root:root wazuh/telegram/custom-cowrie-telegram /app/custom-cowrie-telegram
COPY --chown=root:root docker/entrypoint.py /app/entrypoint.py

RUN chmod 0644 /app/firewall.py /app/entrypoint.py \
    && chmod 0755 /app/custom-cowrie-telegram

USER 10001:10001

ENTRYPOINT ["python3", "/app/entrypoint.py"]
CMD ["--self-test", "--fixtures", "/app/fixtures"]
