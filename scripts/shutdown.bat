@echo off

REM Navigate to the directory containing your docker-compose.prod.yml file
cd .

REM Shut down the Docker containers
docker-compose -f docker-compose.prod.yml down -v