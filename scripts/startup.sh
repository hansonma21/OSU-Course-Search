#!/bin/bash

# Navigate to the directory containing your docker-compose.prod.yml file
cd .

# Start the Docker containers
docker compose -f docker-compose.prod.yml up -d --build

# Collect static files
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear