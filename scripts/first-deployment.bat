@echo off

REM Navigate to the directory containing your docker-compose.prod.yml file
cd .

REM Start the Docker containers and collect static files
call scripts/startup.bat

REM Load data into the database
docker-compose -f docker-compose.prod.yml exec web python manage.py loaddata courses.json
docker-compose -f docker-compose.prod.yml exec web python manage.py loaddata instructors.json
docker-compose -f docker-compose.prod.yml exec web python manage.py loaddata departments.json
docker-compose -f docker-compose.prod.yml exec web python manage.py loaddata terms.json

REM Create a new super user
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser