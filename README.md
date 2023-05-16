# OSU-Course-Search
Django Project, deployed on Heroku, that allows OSU students to search for their classes and find out who their instructors might be (that would otherwise be hidden). A very, very limited build can be viewed on osucoursesearch.herokuapp.com

# Currently in a beta build
To first get all the packages, you need to set up a virtual environment (venv) and run ```pip install -r requirements.txt```
To test locally, you need to run
```python manage.py createsuperuser```
Follow the directions to create an admin profile. From there run
```python manage.py migrate``` to run the migrations

Then load in seed data via:
```python manage.py loaddata search/terms```
```python manage.py loaddata search/departments```
```python manage.py loaddata search/courses```
```python manage.py loaddata search/instructors```

Finally, start the local server via:
```python manage.py runserver```

# 0.0.1
In the beginning, there will be no data, but you can navigate to /admin and login with the credentials you just gave. This will allow you to access an admin page that I created that you can use to create data (e.g. Terms, Instructors, Departments (and their courses), Courses_sections)

The only features available right now (on the homepage) are searching by course number and instructor last name (the only ones that work for now). The data it searches must be supplied by you either in "python manage.py shell" or in the admin page (described in the paragraph above)

# 0.1
There is now plenty of seed data for the departments, courses, terms, and instructors. The departments, courses, and instructors were obtained from osuprofs.com (you can see this in my obtain_seed_data.py file. There is plenty of searching capability now! You must provide a term, but you can then provide a course subject + number OR an instructor name. The instructor name search takes into account both the first and last name, so feel free to search on both.
