from typing import Any
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic
from .forms import SearchForm
from .models import Course_Section
from .filters import Course_SectionFilter

# Create your views here.
# def index(request):
#     return HttpResponse("Hello, world. You're at the polls index.")

# class IndexView(generic.FormView):
#     form_class = SearchForm
#     template_name = "search/index.html"


# class SearchResultsView(generic.ListView):
#     model = Course_Section
#     template_name = "search/search_results.html"
#     form_class = SearchForm
#     context_object_name = "object_list"
    

#     def get_queryset(self):
#         # form = self.form_class(self.request.GET)
#         # if form.is_valid():
#         #     # return Course_Section.objects.filter(course__number__iexact=form.cleaned_data['number'],
#         #     #                             instructors__last_name__iexact=form.cleaned_data['instructor_last_name']
#         #     #                             )
#         #     return Course_Section.objects.filter(term__name__iexact=form.cleaned_data['term'],
#         #                                          course__department__short_name__iexact=form.cleaned_data['department'],
#         #                                          course__number__iexact=form.cleaned_data['number'],
#         #                                          instructors__last_name__iexact=form.cleaned_data['instructor_last_name']
#         #                                          )
#         # else:
#         #     return Course_Section.objects.none()
#         myFilter = Course_SectionFilter(self.request.GET, queryset=Course_Section.objects.all())
#         return myFilter.qs

def index(request):
    """View for index page, will display search form and search results"""

    if request.method == "POST":
        # if the user has submitted the form, create a filter instance and populate it with data from the request
        myFilter = Course_SectionFilter(request.POST)
        course_sections = None

        # check if the filter is valid, if so, get the queryset and pass it to the template
        if myFilter.is_valid():
            print("valid")
            course_sections = myFilter.qs
        
        return render(request, "search/index.html", context={"course_sections": course_sections, "myFilter": myFilter})
    else:
        # if the user has not submitted the form, create an empty filter instance
        myFilter = Course_SectionFilter(request.GET, queryset=Course_Section.objects.all())
        return render(request, "search/index.html", context={"myFilter": myFilter})

# def search(request):
#     if request.method == "POST":
#         form = 
    