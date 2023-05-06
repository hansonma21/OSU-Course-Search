from typing import Any
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic
from .forms import SearchForm
from .models import Course_Section

# Create your views here.
# def index(request):
#     return HttpResponse("Hello, world. You're at the polls index.")

class IndexView(generic.FormView):
    form_class = SearchForm
    template_name = "search/index.html"


class SearchResultsView(generic.ListView):
    model = Course_Section
    template_name = "search/search_results.html"
    form_class = SearchForm
    context_object_name = "object_list"

    def get_queryset(self):
        form = self.form_class(self.request.GET)
        if form.is_valid():
            return Course_Section.objects.filter(
                                        course_term__course__number__iexact=form.cleaned_data['number'],
                                        instructors__last_name__iexact=form.cleaned_data['instructor_last_name']
                                        )
            # return Course_Section.objects.filter(course_term__term__name__iexact=form.cleaned_data['term'],
            #                                      course_term__course__department__short_name__iexact=form.cleaned_data['department'],
            #                                      course_term__course__number__iexact=form.cleaned_data['number'],
            #                                      instructors__last_name__iexact=form.cleaned_data['instructor_last_name']
            #                                      )
        else:
            return Course_Section.objects.none()

# def search(request):
#     if request.method == "POST":
#         form = 
    