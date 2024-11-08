FROM python:3.12-slim

# Install netcat-openbsd to be able to use the nc command in startup scripts
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

WORKDIR /distance_service

COPY pyproject.toml poetry.lock ./

# Copy the start.sh file to the container
COPY ./distance_service/start.sh /start.sh
RUN chmod +x /start.sh

# Set the variables so that the container finds the code
ENV PYTHONPATH=/distance_service
ENV FLASK_ENV=production

RUN pip install poetry

RUN poetry install --no-root --with dev


COPY ./distance_service/ /distance_service/

EXPOSE 5000

CMD ["/start.sh"]
