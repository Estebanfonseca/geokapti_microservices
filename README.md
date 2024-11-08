# Microservices for Registration and Distance Calculation of Delivery Routes

This project implements two microservices as REST API for:

1. Register locations with their coordinates.
2. Calculate the total distance of a route from a list of two locations.

The distance between locations is calculated using the **Haversine formula**, which measures the distance on the spherical surface of the Earth. The architecture is built on top of Docker, using `Flask` ​​for REST APIs and `RabbitMQ` along with `Redis` for asynchronous distance processing.

Additionally, it is worth mentioning that the technologies of RabbitMQ, poetry and redis were a bit unknown to me but here I can show my ability to learn and implement new technologies in a short time.

## Table of Contents

- [Requirements](#requirements)
- [Project Structure](#project-structure)
- [Configuration](#configuration)


## Requirements

- Python 3.12+
- Docker and Docker Compose
- poetry (for dependency management and packaging)

## Project Structure

```plaintext
project-root/
│
├── distance_service/
│   ├── tests/
│   │   ├── test_distance_app.py       # Unit and integration testing
│   │   └── ...
│   ├── __init__.py                
│   ├── app.py                # Distance calculation microservice main code
│   ├── Dockerfile            # Dockerfile
│   └── start.sh              #start of tests and start of application
│
├── location_service/
│   ├── tests/
│   │   ├── test_location_app.py       # Unit and integration testing
│   │   └── ...
│   ├── __init__.py             
│   ├── app.py                # save location microservice main code
│   ├── Dockerfile            # Dockerfile
│   └── start.sh             # start of tests and start of application
│
├── docker-compose.yaml       # Container Orchestration
├── poetrylock
├── pyproject.toml            # Dependency configuration
└── README.md                 # Project documentation   

```


## Configuration

1. Clone the repository.
   ```bash
   git clone https://github.com/Estebanfonseca/geokapti_microservices.git
   ```
2. Install dependencies using poetry.
   ```bash
   poetry install
   ```
3. Build the Docker images.
   ```bash
   docker-compose up -d  --build
   ```
4. The services should be available.
   ```bash
    #calculate distance service
    http://localhost:5000
    #registry location service
    http://localhost:5001
    ```
5. The two services have integrated interactive documentation with Swagger in the root route '/'
Once you access the aforementioned urls you will enter directly into said documentation.

## Resgistry location service
![Resgistry location service](images/Captura%20de%20pantalla%202024-11-08%20124519.png "Resgistry location")

## Calculate Distance service
![Calculate Distance service](images/Captura%20de%20pantalla%202024-11-08%20124535.png "Calculate Distance")
