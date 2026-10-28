FROM python:3.12.16-slim

WORKDIR /location_service

ENV PYTHONPATH=/location_service \
    PYTHONUNBUFFERED=1

COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry==1.8.4 \
    && poetry install --no-root --with dev

COPY ./location_service/start.sh /start.sh
RUN chmod +x /start.sh
COPY ./location_service/ /location_service/

EXPOSE 5001

CMD ["/start.sh"]
