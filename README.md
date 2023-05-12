# OSU-Course-Search
Django Project, deployed on Heroku, that allows OSU students to search for their classes and find out who their instructors might be (that would otherwise be hidden). A very, very limited build can be viewed on osucoursesearch.herokuapp.com

# Currently in a VERY ALPHA build
At the moment, there is no seed data, but you can run
```python manage.py createsuperuser```
Follow the directions to create an admin profile. From there run
```python manage.py migrate```
```python manage.py runserver```
This will run migrations and run a local server of this Django project. 

# 0.1
In the beginning, there will be no data, but you can navigate to /admin and login with the credentials you just gave. This will allow you to access an admin page that I created that you can use to create data (e.g. Terms, Instructors, Departments (and their courses), Courses_sections)

The only features available right now (on the homepage) are searching by course number and instructor last name (the only ones that work for now). The data it searches must be supplied by you either in "python manage.py shell" or in the admin page (described in the paragraph above)
