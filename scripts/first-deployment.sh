#!/bin/bash

# Navigate to the directory containing your docker-compose.prod.yml file
cd .

# Start the Docker containers and collect static files
./scripts/startup.sh

# Load data into the database
docker compose -f docker-compose.prod.yml exec web python manage.py loaddata search/terms.json
docker compose -f docker-compose.prod.yml exec web python manage.py loaddata search/departments.json
docker compose -f docker-compose.prod.yml exec web python manage.py loaddata search/courses.json
docker compose -f docker-compose.prod.yml exec web python manage.py loaddata search/instructors.json

# Create a new super user
docker compose -f docker-compose.prod.yml exec -T web python manage.py createsuperuser