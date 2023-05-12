release: python manage.py migrate
release: python manage.py loaddata search/terms
release: python manage.py loaddata search/departments
release: python manage.py loaddata search/courses
release: python manage.py loaddata search/instructors
web: gunicorn osu_course_search.wsgi
worker: python manage.py qcluster --settings=osu_course_search.settings