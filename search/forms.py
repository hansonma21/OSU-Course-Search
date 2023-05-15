from django import forms
from .models import Department, Course, Instructor, Term

class SearchForm(forms.Form):
    """Search form that is presented on the homepage, will allow users to look up by Term, Course, and Instructor"""
    term = forms.ModelChoiceField(queryset=Term.objects.all()) # commented out for now since it messes up the search for now
    department = forms.ModelChoiceField(queryset=Department.objects.all())
    number = forms.CharField(max_length=Course._meta.get_field('number').max_length, required=False)
    instructor_last_name = forms.CharField(max_length=Instructor._meta.get_field('last_name').max_length, required=False)
