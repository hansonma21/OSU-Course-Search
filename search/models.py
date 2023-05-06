from django.db import models

# Create your models here.
class Term(models.Model):
    """An individual term/semester"""
    osu_id = models.IntegerField() # unique OSU identifier for terms (e.g. 1238)
    name = models.CharField(max_length=4) # e.g. AU23

    def __str__(self):
        return self.name


class Department(models.Model):
    """An individual department; has Courses"""
    name = models.CharField(max_length=50) # e.g. Computer Science and Engineering
    short_name = models.CharField(max_length=20) # e.g. CSE

    def __str__(self):
        return self.short_name


class Course(models.Model):
    """An individual course entity; belongs to a department"""
    name = models.TextField() # e.g. Systems I: Introduction...
    department = models.ForeignKey(Department, on_delete=models.CASCADE) # referencing a Department
    number = models.CharField(max_length=20) # e.g. 2421
    description = models.TextField() # e.g. Introduction to computer architecture at machine...

    def __str__(self):
        return '{} {}'.format(self.department.short_name, self.number)


class Course_Term(models.Model):
    """Representing the many to many relationship between a term/semester and a course, has Course_Sections (individual sections)"""
    term = models.ForeignKey(Term, on_delete=models.CASCADE) # referencing a Term
    course = models.ForeignKey(Course, on_delete=models.CASCADE) # referencing a Course

    def __str__(self):
        return '{}, {}'.format(self.course.__str__(), self.term.name)


class Instructor(models.Model):
    """An individual instructor entity; can belong to many sections"""
    # osu_identifier is only available for salaried staff, not available for all (many instructors are not on salary)
    # osu_identifier = models.IntegerField() # unique OSU identifier for instructors as found in Salary database (e.g. 100098)
    first_name = models.CharField(max_length=50) # e.g. Mukul
    last_name = models.CharField(max_length=50) # e.g. Soundarajan
    department = models.ForeignKey(Department, on_delete=models.CASCADE) # referencing a Department

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Course_Section(models.Model):
    """An individual section entity; belongs to a Course_Term (a Course and a Term), can have many instructors"""
    course_term = models.ForeignKey(Course_Term, on_delete=models.CASCADE) # referencing a Course_Term
    
    instructors = models.ManyToManyField(Instructor) # only need one many to many field to represent many to many relationship of sections and instructors

    section_id = models.IntegerField() # e.g. 9510
    section_info = models.CharField(max_length=20) # e.g. LEC-0010
    days_and_times = models.CharField(max_length=50) # e.g. TuTh 9:35AM - 10:55 AM
    start_date = models.DateTimeField() # e.g. 08/22/2023
    end_date = models.DateTimeField() # e.g. 12/06/2023
    room = models.CharField(max_length=50) # e.g. McPherson Lab 2015
    availability = models.CharField(max_length=15) # one of Available, Waitlist, or Closed

    def __str__(self):
        return '{}, {}'.format(self.course_term.__str__(), self.section_id)

