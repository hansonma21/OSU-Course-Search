from django.db import models

# Create your models here.
class Term(models.Model):
    """An individual term/semester; has Courses"""
    osu_id = models.IntegerField() # unique OSU identifier for terms (e.g. 1238)
    name = models.CharField(max_length=4) # e.g. AU23
    display_boolean = models.BooleanField(default=True) # whether or not to display the term in the UI

    # ensures that the osu_id and name are unique
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['osu_id'], name='unique_term_osu_id'),
            models.UniqueConstraint(fields=['name'], name='unique_term_name')
        ]

    def __str__(self):
        return self.name


class DepartmentManager(models.Manager):
    """A manager for Department objects; used to filter by department short_name"""
    def get_by_natural_key(self, short_name):
        return self.get(short_name=short_name)

class Department(models.Model):
    """An individual department; has Courses"""
    name = models.CharField(max_length=50) # e.g. Computer Science and Engineering
    short_name = models.CharField(max_length=20) # e.g. CSE

    # allows access to Department objects by short_name
    objects = DepartmentManager()

    # ensures that the short_name and name are unique
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name'], name='unique_department_name'),
            models.UniqueConstraint(fields=['short_name'], name='unique_department_short_name')
        ]

    def __str__(self):
        return self.short_name


class CourseManager(models.Manager):
    """A manager for Course objects; used to filter by department short_name and course number"""
    def get_by_natural_key(self, department_short_name, number):
        return self.get(department__short_name=department_short_name, number=number)

class Course(models.Model):
    """An individual course entity; belongs to a department; belongs to many terms"""
    name = models.TextField(null=True) # e.g. Systems I: Introduction...
    department = models.ForeignKey(Department, on_delete=models.CASCADE) # referencing a Department
    number = models.CharField(max_length=20) # e.g. 2421
    description = models.TextField(null=True) # e.g. Introduction to computer architecture at machine...

    created_date = models.DateTimeField(auto_now_add=True, null=True) # e.g. 2023-08-22 09:35:00
    updated_date = models.DateTimeField(auto_now=True, null=True) # e.g. 2023-08-22 09:35:00

    terms = models.ManyToManyField(Term) # many to many relationship with Term

    # allows access to Course objects by department short_name and course number
    objects = CourseManager()

    # ensures that the department and number are unique
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['department', 'number'], name='unique_course_department_number')
        ]

    def __str__(self):
        return '{} {}'.format(self.department.short_name, self.number)


# class Course_Term(models.Model):
#     """Representing the many to many relationship between a term/semester and a course, has Course_Sections (individual sections)"""
#     term = models.ForeignKey(Term, on_delete=models.CASCADE) # referencing a Term
#     course = models.ForeignKey(Course, on_delete=models.CASCADE) # referencing a Course

#     # ensures that the term and course are unique
#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=['term', 'course'], name='unique_course_term')
#         ]

#     def __str__(self):
#         return '{}, {}'.format(self.course.__str__(), self.term.name)


class Instructor(models.Model):
    """An individual instructor entity; can belong to many sections"""
    # osu_identifier is only available for salaried staff, not available for all (many instructors are not on salary)
    # osu_identifier = models.IntegerField() # unique OSU identifier for instructors as found in Salary database (e.g. 100098)
    first_name = models.CharField(max_length=100) # e.g. Mukul
    last_name = models.CharField(max_length=100) # e.g. Soundarajan
    department = models.ForeignKey(Department, on_delete=models.CASCADE) # referencing a Department

    created_date = models.DateTimeField(auto_now_add=True, null=True) # e.g. 2023-08-22 09:35:00
    updated_date = models.DateTimeField(auto_now=True, null=True) # e.g. 2023-08-22 09:35:00

    # ensures that the first_name, last_name, and department are unique
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['first_name', 'last_name', 'department'], name='unique_instructor_first_last_department')
        ]

        ordering=('last_name', 'first_name')

    def __str__(self):
        return '{} {}, {}'.format(self.first_name, self.last_name, self.department.short_name)


class Course_Section(models.Model):
    """An individual section entity; belongs to Course and a Term, can have many instructors"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE) # referencing a Course
    term = models.ForeignKey(Term, on_delete=models.CASCADE) # referencing a Term
    link_number = models.IntegerField(null=True) # link multiple course sections together (linked sections have the same link_number)

    created_date = models.DateTimeField(auto_now_add=True, null=True) # e.g. 2023-08-22 09:35:00
    updated_date = models.DateTimeField(auto_now=True, null=True) # e.g. 2023-08-22 09:35:00

    instructors = models.ManyToManyField(Instructor) # only need one many to many field to represent many to many relationship of sections and instructors

    section_id = models.IntegerField() # e.g. 9510
    section_info = models.TextField(null=True) # e.g. LEC-0010
    days_and_times = models.TextField(null=True) # e.g. TuTh 9:35AM - 10:55 AM
    start_date = models.DateField(null=True) # e.g. 08/22/2023
    end_date = models.DateField(null=True) # e.g. 12/06/2023
    room = models.TextField(null=True) # e.g. McPherson Lab 2015
    availability = models.CharField(max_length=15, null=True) # one of Available, Waitlist, or Closed

    barrett_data_json = models.JSONField(null=True) # JSON data of course_section info from Barrett source
    # stores "type", "autoenrolls", "days", "time", "location", "enrolled", "limit", "waitlist", "duration", "instructors"

    # ensures that the term and section_id are unique
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['term', 'section_id'], name='unique_term_section_id'),
        ]

    def __str__(self):
        course_and_term_str = '{}, {}'.format(self.course.__str__(), self.term.name)
        instructors_str = ['{} {}'.format(instructor.first_name, instructor.last_name) for instructor in self.instructors.all().iterator()]
        return '{}, {}; Instructors: {}'.format(course_and_term_str, self.section_id, instructors_str)

class Search_Query(models.Model):
    """An individual search query entity; stores search queries"""
    # no foreign keys, just store the search query and timestamp so we can see what users are searching for and when
    # no foreign keys guarantees that we can store any search query, even if it doesn't match a course section 
    # (and on deletion of course sections, we don't delete search queries)
    # e.g. {"term": "AU23", "subject": "CSE", "number": "2421", "instructor": "LaTour"}
    search_query = models.JSONField(null=True) # JSON data of search query
    # stores "term" (e.g. AU23), "subject" (e.g. CSE), "number" (e.g. 2421), "instructor" (e.g. LaTour)
    timestamp = models.DateTimeField(auto_now_add=True) # e.g. 2023-08-22 09:35:00

    def __str__(self):
        return '{} - {}'.format(self.search_query, self.timestamp.strftime('%Y-%m-%d %H:%M:%S'))

class Error_Log(models.Model):
    """An individual error log entity; stores error messages"""
    error_message = models.TextField() # e.g. Error message here
    stack_trace = models.TextField(null=True) # e.g. Stack trace here
    function_name = models.TextField(null=True) # e.g. Function name here
    additional_info = models.TextField(null=True) # e.g. Additional info here
    timestamp = models.DateTimeField(auto_now_add=True) # e.g. 2023-08-22 09:35:00

    def __str__(self):
        return '{}: {} - {}'.format(self.function_name, self.error_message, self.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
    
class News(models.Model):
    """A model to store news/updates articles"""
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    display = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date_posted']
    
    def __str__(self):
        return self.title