import pytest
from app import app
import redis
import json

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

@pytest.fixture
def redis_client():
    # Configuring the Redis client that connects to the Redis container
    client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)
    yield client
    client.flushdb()  # Clean Redis after testing to avoid residual data


def test_full_distance_calculation_flow(client, redis_client):
    # Define test locations
    location_1 = {"name": "Nueva York", "latitude": 40.7128, "longitude": -74.0060}  # Nueva York
    location_2 = {"name": "Los Ángeles", "latitude": 34.0522, "longitude": -118.2437} # Los Ángeles

    # Save locations in Redis
    redis_client.set("loc1", json.dumps( location_1))
    redis_client.set("loc2", json.dumps( location_2))

    # Send POST request to calculate distance
    response_post = client.post('/calculate_distance', json={"location_ids": ["loc1","loc2"]})
    assert response_post.status_code == 202

    # Make the GET request to get the distance result
    response_get = client.get('/distance_result')
    
    # Verify that the result is as expected
    assert response_get.status_code == 200
    assert response_get.is_json
    assert response_get.get_json() == {"total_distance": 3935.746254609723}
