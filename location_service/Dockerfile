FROM python:3.12-slim

WORKDIR /location_service

COPY pyproject.toml poetry.lock ./

# Copy the start.sh file to the container
COPY ./location_service/start.sh /start.sh
RUN chmod +x /start.sh

# Set the variables so that the container finds the code
ENV PYTHONPATH=/location_service
ENV FLASK_ENV=production

RUN pip install poetry

RUN poetry install --no-root --with dev


COPY ./location_service/ /location_service/

EXPOSE 5000

# Run the Flask server
CMD ["/start.sh"]
