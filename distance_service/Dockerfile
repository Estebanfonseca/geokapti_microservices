FROM python:3.12.16-slim

WORKDIR /distance_service

ENV PYTHONPATH=/distance_service \
    PYTHONUNBUFFERED=1

COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry==1.8.4 \
    && poetry install --no-root --with dev

COPY ./distance_service/start.sh /start.sh
RUN chmod +x /start.sh
COPY ./distance_service/ /distance_service/

EXPOSE 5000

CMD ["/start.sh"]
