#!/bin/bash

# Esperar a que RabbitMQ esté disponible
while ! nc -z rabbitmq 5672; do
  echo "Esperando a que RabbitMQ esté listo..."
  sleep 1
done
echo "RabbitMQ está listo, iniciando las pruebas"

# Ejecutar las pruebas con poetry
poetry run pytest -v --tb=long --maxfail=1

# Verificar si las pruebas fueron exitosas
if [ $? -eq 0 ]; then
  echo "Las pruebas fueron exitosas, iniciando el servidor Flask"
  poetry run flask run --host=0.0.0.0 --port=5000 
else
  echo "Las pruebas fallaron, no se iniciará el servidor Flask"
  exit 1
fi
