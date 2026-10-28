import json
import math
import os

import pika
import redis
import structlog
from flask import Flask
from flask.views import MethodView
from flask_smorest import Api, Blueprint, abort
from marshmallow import Schema, fields

# App and API settings
app = Flask(__name__)
app.config["API_TITLE"] = "GeoKapti API Calculate Distance"
app.config["API_VERSION"] = "1.0"
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

logger = structlog.get_logger()

r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=int(os.getenv("REDIS_DB", "0")),
)

api = Api(app)
blp = Blueprint(
    "distance",
    "distance",
    url_prefix="",
    description="Calculates distances between locations",
)


class LocationIdsSchema(Schema):
    location_ids = fields.List(
        fields.String(),
        required=True,
        metadata={"description": "Exactly two registered location IDs"},
    )


class DistanceRequestStatusSchema(Schema):
    status = fields.String(
        metadata={"description": "Status of the distance calculation request"}
    )


class DistanceResultSchema(Schema):
    total_distance = fields.Float(
        metadata={"description": "Great-circle distance in kilometers"}
    )


def get_location_from_redis(location_id):
    location_data = r.get(location_id)
    if location_data:
        return json.loads(location_data)
    return None


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two coordinates in kilometers."""
    earth_radius_km = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * c


def rabbitmq_connection_parameters():
    credentials = pika.PlainCredentials(
        os.environ["RABBITMQ_USER"],
        os.environ["RABBITMQ_PASSWORD"],
    )
    return pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
        port=int(os.getenv("RABBITMQ_PORT", "5672")),
        credentials=credentials,
    )


def send_to_queue(message):
    connection = None
    try:
        connection = pika.BlockingConnection(rabbitmq_connection_parameters())
        channel = connection.channel()
        channel.queue_declare(queue="result_queue")
        channel.basic_publish(exchange="", routing_key="result_queue", body=message)
        logger.info("Distance result published", queue="result_queue")
    except pika.exceptions.AMQPError as error:
        logger.error(
            "Failed to publish distance result",
            error_type=type(error).__name__,
        )
        abort(500, message="Failed to publish distance result")
    finally:
        if connection is not None and connection.is_open:
            connection.close()


@blp.route("/calculate_distance")
class CalculateDistanceResource(MethodView):
    @blp.arguments(LocationIdsSchema)
    @blp.response(202, DistanceRequestStatusSchema)
    @blp.alt_response(400, description="Exactly two location IDs are required")
    @blp.alt_response(404, description="A requested location was not found")
    @blp.alt_response(500, description="The result could not be published")
    def post(self, args):
        """Calculate and enqueue the distance between two registered locations."""
        location_ids = args["location_ids"]
        if len(location_ids) != 2:
            abort(
                400,
                message="Exactly two location IDs are required to calculate distance.",
            )

        locations = []
        for location_id in location_ids:
            location_data = get_location_from_redis(location_id)
            if location_data is None:
                logger.info("Location not found", location_id=location_id)
                abort(404, message=f"Location not found for ID: {location_id}")
            locations.append(location_data)

        distance = haversine(
            locations[0]["latitude"],
            locations[0]["longitude"],
            locations[1]["latitude"],
            locations[1]["longitude"],
        )

        send_to_queue(str(distance))
        logger.info("Distance calculated", location_count=len(location_ids))
        return {"status": "Request sent to calculate distance"}


@blp.route("/distance_result")
class DistanceResultResource(MethodView):
    @blp.response(200, DistanceResultSchema)
    @blp.alt_response(204, description="No distance result is available")
    @blp.alt_response(500, description="The result queue is unavailable")
    def get(self):
        """Retrieve and acknowledge the next distance result."""
        connection = None
        try:
            connection = pika.BlockingConnection(rabbitmq_connection_parameters())
            channel = connection.channel()
            channel.queue_declare(queue="result_queue")
            method_frame, _, body = channel.basic_get(
                queue="result_queue",
                auto_ack=False,
            )

            if body is None:
                logger.info("No distance result available", queue="result_queue")
                return "", 204

            total_distance = float(body.decode("utf-8"))
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            logger.info("Distance result retrieved")
            return {"total_distance": total_distance}
        except pika.exceptions.AMQPError as error:
            logger.error(
                "Failed to retrieve distance result",
                error_type=type(error).__name__,
            )
            abort(500, message="Could not retrieve the distance result")
        finally:
            if connection is not None and connection.is_open:
                connection.close()


api.register_blueprint(blp)
