release: python manage.py migrate
web: gunicorn osu_course_search.wsgi
worker: python manage.py qcluster