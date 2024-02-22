@echo off

REM Navigate to the directory containing your docker-compose.prod.yml file
cd .

REM Shut down the Docker containers
docker-compose -f docker-compose.prod.yml down -v

REM Start the Docker containers
docker-compose -f docker-compose.prod.yml up -d --build

REM Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --no-input --clear