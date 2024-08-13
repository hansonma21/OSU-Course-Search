import django_filters
from django.db.models import Q
from .models import *

class Course_SectionFilter(django_filters.FilterSet):
    """Filter for Course_Section model, will allow users to filter by Term, Course, and Instructor"""
    term = django_filters.ModelChoiceFilter(field_name='term__name', queryset=Term.objects.filter(display_boolean=True), label='Term') # term is the term (e.g. Spring 2021) - ModelChoiceField
    subject = django_filters.AllValuesFilter(field_name='course__department__short_name', label='Subject') # subject is the department (e.g. CSE) - ChoiceField
    number = django_filters.CharFilter(field_name='course__number', method='filter_by_number') # number is the course number (e.g. 2421) - CharField
    instructor = django_filters.CharFilter(field_name='instructors', method='filter_by_instructor', label='Instructor') # instructor is the instructor's name- CharField

    class Meta:
        model = Course_Section
        fields = ['term'] # auto term filter

    # def __init__(self, *args, **kwargs):
    #     super(Course_SectionFilter, self).__init__(*args, **kwargs)
    #     # at startup user doen't push Submit button, and QueryDict (in data) is empty
    #     if self.data == {}:
    #         self.queryset = self.queryset.none()

    def __init__(self, *args, **kwargs):
        super(Course_SectionFilter, self).__init__(*args, **kwargs)
        self.filters['term'].field.empty_label = 'Select Term'
        self.filters['subject'].field.empty_label = 'Select Subject'
        self.filters['number'].field.widget.attrs['placeholder'] = 'e.g. 2421'
        self.filters['instructor'].field.widget.attrs['placeholder'] = 'e.g. Rob LaTour'

        self.filters['term'].field.widget.attrs.update({'class': "w-full bg-white border border-gray-300 rounded py-2 px-4 block appearance-none leading-normal"})
        self.filters['subject'].field.widget.attrs.update({'class': "w-full bg-white border border-gray-300 rounded py-2 px-4 block appearance-none leading-normal"})
        self.filters['number'].field.widget.attrs.update({'class': "w-full bg-white border border-gray-300 rounded py-2 px-4 block appearance-none leading-normal"})
        self.filters['instructor'].field.widget.attrs.update({'class': "w-full bg-white border border-gray-300 rounded py-2 px-4 block appearance-none leading-normal"})

    def is_valid(self):
        """Override is_valid to check if term is present and either course or instructor is present"""

        subject_search = self.data.get('subject', '')
        number_search = self.data.get('number', '')

        is_term_present = self.data.get('term', '') != ''
        is_course_search = subject_search != '' and number_search != ''
        is_instructor_search = self.data.get('instructor', None) != ''
        return is_term_present and (is_course_search or is_instructor_search)
        
    # custom filter for course number that filters by exact match or prefix match (e.g. 2421 or 24)
    def filter_by_number(self, queryset, name, value):
        return queryset.filter(Q(course__number__iexact=value) | Q(course__number__startswith=value))
    
    # custom filter for instructor that filters by first name or last name (e.g. Rob LaTour or Rob or LaTour or Rob L, etc.)
    def filter_by_instructor(self, queryset, name, value):
        for term in value.split():
            queryset = queryset.filter(Q(instructors__first_name__icontains = term) | Q(instructors__last_name__icontains = term) | Q(barrett_data_json__instructors__icontains = term))
        return queryset