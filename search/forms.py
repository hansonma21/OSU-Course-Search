from django import forms
from .models import Department, Course, Instructor

class SearchForm(forms.Form):
    term = forms.ChoiceField()
    department = forms.ChoiceField()
    number = forms.CharField(max_length=Course._meta.get_field('number').max_length)
    instructor_last_name = forms.CharField(max_length=Instructor._meta.get_field('last_name').max_length)
