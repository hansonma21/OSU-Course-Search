from django import forms
from .models import Department, Course, Instructor

class SearchForm(forms.Form):
    """Search form that is presented on the homepage, will allow users to look up by Term, Course, and Instructor"""
    # term = forms.ChoiceField() # commented out for now since it messes up the search for now
    # department = forms.ChoiceField()
    number = forms.CharField(max_length=Course._meta.get_field('number').max_length)
    instructor_last_name = forms.CharField(max_length=Instructor._meta.get_field('last_name').max_length)
