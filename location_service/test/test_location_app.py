import pytest
from app import app, r
import json

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_register_location(client):
    location_data = {
        "name": "Test Location",
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    response = client.post('/locations', json=location_data)
    assert response.status_code == 201
    location_id = response.json["id"]

    # Verify that the location has been saved in Redis
    saved_location = r.get(location_id)
    assert saved_location is not None

    # Verify that the data is correct
    saved_location = json.loads(saved_location)
    assert saved_location["name"] == location_data["name"]
    assert saved_location["latitude"] == location_data["latitude"]
    assert saved_location["longitude"] == location_data["longitude"]

