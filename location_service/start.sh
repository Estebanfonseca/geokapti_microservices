#!/bin/bash

# Run the tests with poetry
poetry run pytest -v --tb=long --maxfail=1

# Check if the tests were successful
if [ $? -eq 0 ]; then
  echo "Las pruebas fueron exitosas, iniciando el servidor Flask"
  poetry run flask run --host=0.0.0.0 --port=5001
else
  echo "Las pruebas fallaron, no se iniciará el servidor Flask"
  exit 1
fi
