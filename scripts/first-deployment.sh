#!/bin/bash

# Navigate to the directory containing your docker-compose.prod.yml file
cd .

# Start the Docker containers and collect static files
./scripts/startup.sh

# Load data into the database
docker-compose -f docker-compose.prod.yml exec -T web python manage.py loaddata courses.json
docker-compose -f docker-compose.prod.yml exec -T web python manage.py loaddata instructors.json
docker-compose -f docker-compose.prod.yml exec -T web python manage.py loaddata departments.json
docker-compose -f docker-compose.prod.yml exec -T web python manage.py loaddata terms.json

# Create a new super user
docker-compose -f docker-compose.prod.yml exec -T web python manage.py createsuperuser