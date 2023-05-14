from django.db import models

# Create your models here.
class Term(models.Model):
    """An individual term/semester; has Courses"""
    osu_id = models.IntegerField() # unique OSU identifier for terms (e.g. 1238)
    name = models.CharField(max_length=4) # e.g. AU23

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
    name = models.TextField() # e.g. Systems I: Introduction...
    department = models.ForeignKey(Department, on_delete=models.CASCADE) # referencing a Department
    number = models.CharField(max_length=20) # e.g. 2421
    description = models.TextField(null=True) # e.g. Introduction to computer architecture at machine...

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
    first_name = models.CharField(max_length=50) # e.g. Mukul
    last_name = models.CharField(max_length=50) # e.g. Soundarajan
    department = models.ForeignKey(Department, on_delete=models.CASCADE) # referencing a Department

    # ensures that the first_name, last_name, and department are unique
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['first_name', 'last_name', 'department'], name='unique_instructor_first_last_department')
        ]

        ordering=('last_name', 'first_name')

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Course_Section(models.Model):
    """An individual section entity; belongs to Course and a Term, can have many instructors"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE) # referencing a Course
    term = models.ForeignKey(Term, on_delete=models.CASCADE) # referencing a Term

    instructors = models.ManyToManyField(Instructor) # only need one many to many field to represent many to many relationship of sections and instructors

    section_id = models.IntegerField() # e.g. 9510
    section_info = models.CharField(max_length=20) # e.g. LEC-0010
    days_and_times = models.CharField(max_length=50) # e.g. TuTh 9:35AM - 10:55 AM
    start_date = models.DateField() # e.g. 08/22/2023
    end_date = models.DateField() # e.g. 12/06/2023
    room = models.CharField(max_length=50) # e.g. McPherson Lab 2015
    availability = models.CharField(max_length=15) # one of Available, Waitlist, or Closed

    # ensures that the term and section_id are unique
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['term', 'section_id'], name='unique_term_section_id')
        ]

    def __str__(self):
        course_and_term_str = '{}, {}'.format(self.course.__str__(), self.term.name)
        return '{}, {}'.format(course_and_term_str, self.section_id)

