import structlog
from flask import Flask, jsonify
import redis
import uuid
from flask_smorest import Api, Blueprint, abort
from marshmallow import Schema, fields
from flask.views import MethodView
import json

# App and API settings
app = Flask(__name__)
app.config['API_TITLE'] = 'GeoKapt API Locations'
app.config['API_VERSION'] = '1.0'
app.config['OPENAPI_VERSION'] = '3.0.2'
app.config['OPENAPI_URL_PREFIX'] = '/'  
app.config['OPENAPI_SWAGGER_UI_PATH'] = ''  
app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'

# Configuring structlog for event logging
logger = structlog.get_logger()

# Connecting to Redis
r = redis.Redis(host='redis', port=6379, db=0)

# Verify connection to Redis
try:
    # Trying to do a simple operation with Redis
    r.ping()
    logger.info("Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    logger.error(f"Failed to connect to Redis: {str(e)}")

# API initialization with Flask-Smorest
api = Api(app)

# Create a Blueprint for location-related endpoints
blp = Blueprint('locations', 'locations', url_prefix='/locations', description="Manages locations")

# Schema to validate location input
class LocationSchema(Schema):
    name = fields.String(required=True, description="Name of the location")
    latitude = fields.Float(required=True, description="Latitude of the location")
    longitude = fields.Float(required=True, description="Longitude of the location")

# Schema for registered location response
class LocationResponseSchema(Schema):
    id = fields.String(description="Unique ID of the registered location")

# Endpoint to register a location
@blp.route('', methods=['POST'])
class RegisterLocationResource(MethodView):
    @blp.arguments(LocationSchema)
    @blp.response(201, LocationResponseSchema)
    def post(self, args):
        
        """Register a new location"""
        
        name = args['name']
        latitude = args['latitude']
        longitude = args['longitude']

        # Generate a unique ID for the location
        location_id = str(uuid.uuid4())
        
        # Save location in Redis
        location_data = {
            "name": name,
            "latitude": latitude,
            "longitude": longitude
        }
        r.set(location_id, json.dumps(location_data))  # Convert to JSON before storing

        # Registrar el evento
        logger.info("Location registered", id=location_id, data=location_data)

        # Verify that data has been saved correctly
        saved_data = r.get(location_id)
        if saved_data:
            logger.info("Location successfully saved in Redis", location_id=location_id, saved_data=json.loads(saved_data))
        else:
            logger.error(f"Failed to retrieve location data for ID {location_id}")

        #Return the ID of the registered location
        return {"id": location_id}, 201

# Endpoint to get registered location
@blp.route('/<string:location_id>', methods=['GET'])
class GetLocationResource(MethodView):
    @blp.response(200, LocationResponseSchema)
    @blp.response(404, description="Location not found")
    def get(self, location_id):
        
        """Retrieve a location by its ID"""
        
        # Get location from Redis
        location_data = r.get(location_id)

        if location_data:
            location_data = json.loads(location_data)
            logger.info("Location retrieved successfully", location_id=location_id, location_data=location_data)
            return {"id": location_id, "name": location_data['name'], "latitude": location_data['latitude'], "longitude": location_data['longitude']}, 200
        else:
            logger.error(f"Location not found for ID {location_id}")
            return {"status": "Location not found"}, 404

# Register the Blueprint in the API
api.register_blueprint(blp)

