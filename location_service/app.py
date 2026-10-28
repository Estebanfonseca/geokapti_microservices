import json
import os
import uuid

import redis
import structlog
from flask import Flask
from flask.views import MethodView
from flask_smorest import Api, Blueprint
from marshmallow import Schema, fields, validate

# App and API settings
app = Flask(__name__)
app.config["API_TITLE"] = "GeoKapti API Locations"
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
    "locations",
    "locations",
    url_prefix="/locations",
    description="Manages locations",
)


class LocationSchema(Schema):
    name = fields.String(
        required=True,
        metadata={"description": "Name of the location"},
    )
    latitude = fields.Float(
        required=True,
        validate=validate.Range(min=-90, max=90),
        metadata={"description": "Latitude in decimal degrees (-90 to 90)"},
    )
    longitude = fields.Float(
        required=True,
        validate=validate.Range(min=-180, max=180),
        metadata={"description": "Longitude in decimal degrees (-180 to 180)"},
    )


class LocationCreatedSchema(Schema):
    id = fields.String(
        metadata={"description": "Unique ID of the registered location"}
    )


class LocationResponseSchema(LocationSchema):
    id = fields.String(
        metadata={"description": "Unique ID of the registered location"}
    )


@blp.route("")
class RegisterLocationResource(MethodView):
    @blp.arguments(LocationSchema)
    @blp.response(201, LocationCreatedSchema)
    def post(self, args):
        """Register a new location."""
        location_id = str(uuid.uuid4())
        location_data = {
            "name": args["name"],
            "latitude": args["latitude"],
            "longitude": args["longitude"],
        }

        r.set(location_id, json.dumps(location_data))
        logger.info("Location registered", location_id=location_id)

        return {"id": location_id}


@blp.route("/<string:location_id>")
class GetLocationResource(MethodView):
    @blp.response(200, LocationResponseSchema)
    @blp.alt_response(404, description="Location not found")
    def get(self, location_id):
        """Retrieve a location by its ID."""
        location_data = r.get(location_id)

        if location_data is None:
            logger.info("Location not found", location_id=location_id)
            return {"status": "Location not found"}, 404

        location = json.loads(location_data)
        logger.info("Location retrieved", location_id=location_id)
        return {"id": location_id, **location}


api.register_blueprint(blp)
