import django_filters
from django.db.models import Q
from .models import *

class Course_SectionFilter(django_filters.FilterSet):
    """Filter for Course_Section model, will allow users to filter by Term, Course, and Instructor"""
    subject = django_filters.AllValuesFilter(field_name='course__department__short_name', label='Subject') # subject is the department (e.g. CSE) - ChoiceField
    number = django_filters.CharFilter(field_name='course__number', method='filter_by_number') # number is the course number (e.g. 2421) - CharField
    instructor = django_filters.CharFilter(field_name='instructors', method='filter_by_instructor', label='Instructor') # instructor is the instructor's name- CharField

    class Meta:
        model = Course_Section
        fields = ['term'] # auto term filter
        
    # custom filter for course number that filters by exact match or prefix match (e.g. 2421 or 24)
    def filter_by_number(self, queryset, name, value):
        return queryset.filter(Q(course__number__iexact=value) | Q(course__number__startswith=value))
    
    # custom filter for instructor that filters by first name or last name (e.g. Rob LaTour or Rob or LaTour or Rob L, etc.)
    def filter_by_instructor(self, queryset, name, value):
        for term in value.split():
            queryset = queryset.filter( Q(instructors__first_name__icontains = term) | Q(instructors__last_name__icontains = term))
        return queryset