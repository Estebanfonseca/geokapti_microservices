import structlog
from flask import Flask, jsonify, request, abort
import pika
import redis
import json
from flask_smorest import Api, Blueprint
from marshmallow import Schema, fields
from flask.views import MethodView
import math

# App and API settings
app = Flask(__name__)
app.config['API_TITLE'] = 'GeoKapti API Calculate Distance'
app.config['API_VERSION'] = '1.0'
app.config['OPENAPI_VERSION'] = '3.0.2'
app.config['OPENAPI_URL_PREFIX'] = '/'
app.config['OPENAPI_SWAGGER_UI_PATH'] = ''
app.config['OPENAPI_SWAGGER_UI_URL'] = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'

# Configuring structlog for logging
logger = structlog.get_logger()

# Connecting to Redis
r = redis.Redis(host='redis', port=6379, db=0)

# API initialization with Flask-Smorest
api = Api(app)

# Create a Blueprint for endpoints related to distance calculation
blp = Blueprint('distance', 'distance', url_prefix='', description="Calculates distances between locations")

# Schema for input validation
class LocationIdsSchema(Schema):
    location_ids = fields.List(fields.String, required=True, metadata={"description": "List of location IDs to calculate distance"})

# Schema for calculation answer
class DistanceRequestStatusSchema(Schema):
    status = fields.String(metadata={"description": "Status of the distance calculation request"})

# Schema for the response of the distance result
class DistanceResultSchema(Schema):
    total_distance = fields.Float(metadata={"description": "Total calculated distance between locations"})

class NotFoundSchema(Schema):
    status = fields.String(metadata={"description": "Status message indicating no results are available"})

# Function to retrieve data from Redis using IDs
def get_location_from_redis(location_id):
    location_data = r.get(location_id)
    if location_data:
        return json.loads(location_data)
    return None

# Haversine formula to calculate the distance between two points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c  # Result in kilometers
    return distance

# Function to send the message to RabbitMQ queue
def send_to_queue(message):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='result_queue')
        channel.basic_publish(exchange='', routing_key='result_queue', body=message)
        connection.close()
        logger.info("Message sent to RabbitMQ", message=message)
    except pika.exceptions.AMQPConnectionError as e:
        logger.error("Failed to connect to RabbitMQ", error=str(e))
        abort(500, message="Failed to send message to RabbitMQ")

# Callback to process RabbitMQ messages
def callback(ch, method, properties, body):
    total_distance = float(body.decode('utf-8'))
    logger.info("Distance result retrieved", total_distance=total_distance)
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Function to get results from RabbitMQ queue
def get_result_from_queue():
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()

    # Declare the queue result_queue
    channel.queue_declare(queue='result_queue')
    logger.info("Queue 'result_queue' declared successfully")

    # Consume the message
    channel.basic_consume(queue='result_queue', on_message_callback=callback)

    # This method will block execution until the message is consumed
    channel.start_consuming()

# Endpoint to calculate distance
@blp.route('/calculate_distance', methods=['POST'])
class CalculateDistanceResource(MethodView):
    @blp.arguments(LocationIdsSchema)
    @blp.response(202, DistanceRequestStatusSchema)
    def post(self, args):
        """Request distance calculation"""
        location_ids = args['location_ids']
        
        # Retrieve Redis locations using IDs
        locations = []
        for location_id in location_ids:
            location_data = get_location_from_redis(location_id)
            if location_data:
                locations.append(location_data)
            else:
                logger.error(f"Location not found in Redis for ID: {location_id}")
                abort(404, message=f"Location not found for ID: {location_id}")
        
        # Verify that the necessary locations were obtained
        if len(locations) != 2:
            abort(400, message="Exactly two location IDs are required to calculate distance.")
        
        # Calculate the distance between the two locations using the Haversine formula
        lat1, lon1 = locations[0]['latitude'], locations[0]['longitude']
        lat2, lon2 = locations[1]['latitude'], locations[1]['longitude']
        distance = haversine(lat1, lon1, lat2, lon2)

        # Send the result to the result_queue queue
        send_to_queue(str(distance))
        logger.info(f"Distance calculated: {distance} km", location_ids=location_ids)

        return {"status": "Request sent to calculate distance"}, 202

# Endpoint to get the calculated distance result
@blp.route('/distance_result', methods=['GET'])
class DistanceResultResource(MethodView):
    @blp.response(200, DistanceResultSchema)
    @blp.response(204, NotFoundSchema)
    def get(self):
        """Retrieve the distance result"""
        try:
            # RabbitMQ connection and channel
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
            channel = connection.channel()

            # Declare result_queue before getting messages
            channel.queue_declare(queue='result_queue')
            logger.info("Queue 'result_queue' declared successfully")

            # Get message from queue result_queue
            method_frame, header_frame, body = channel.basic_get(queue='result_queue')
            
            if body is None:
                logger.info("No messages found in 'result_queue'")
                connection.close()
                return jsonify({"status": "No results available"}), 204

            # Get and return the distance result
            total_distance = float(body.decode('utf-8'))
            logger.info("Distance result retrieved", total_distance=total_distance)
            connection.close()
            return jsonify({"total_distance": total_distance}), 200

        except pika.exceptions.AMQPConnectionError as e:
            logger.error("Failed to connect to RabbitMQ", error=str(e))
            abort(500, message="Could not connect to RabbitMQ")

# Register the Blueprint in the API
api.register_blueprint(blp)
