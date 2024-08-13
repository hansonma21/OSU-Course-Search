import traceback
from typing import Any
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic
from .forms import SearchForm
from .models import Course, Course_Section, Department, Error_Log, Search_Query, Term, News
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

    def save_query(myFilter: Course_SectionFilter):
        try:
            # obtain each of the values from myFilter
            term = myFilter.data.get('term', '')
            subject = myFilter.data.get('subject', '')
            number = myFilter.data.get('number', '')
            instructor = myFilter.data.get('instructor', '')

            # get the term name from the term id
            term_name = ''
            if term != '':
                try:
                    term_name = Term.objects.get(id=term).name
                except Exception as E:
                    term_name = ''
            
            # create a Search_Query object to store the search parameters
            search_query = {
                "term": term_name,
                "subject": subject,
                "number": number,
                "instructor": instructor
            }
        
        
            new_search_query = Search_Query.objects.create(search_query=search_query)
            new_search_query.save()
        except Exception as E:
            # write the error to the error logs
            error_message = "Error saving search query for term: {}, subject: {}, number: {}, instructor: {}".format(term_name, subject, number, instructor)
            error_log = Error_Log.objects.create(error_message=error_message,
                                                  stack_trace=traceback.format_exc(),
                                                  function_name="views.index.save_query")
            error_log.save()


    if request.method == "POST":
        # if the user has submitted the form, create a filter instance and populate it with data from the request
        myFilter = Course_SectionFilter(request.POST)
        course_dict = None
        error_message = None

        save_query(myFilter)

        # check if the filter is valid, if so, get the queryset and pass it to the template
        if myFilter.is_valid():
            course_sections = myFilter.qs

            if course_sections.exists():
                if course_sections.count() > 250:
                    error_message = "Too many results found. Please narrow your search."
                else:
                    course_id_list = course_sections.values_list('course').distinct()
                    courses = Course.objects.filter(id__in=course_id_list).order_by('department__short_name', 'number').iterator()

                    course_dict = {}
                    for course in courses:
                        course_sections_for_course = course_sections.filter(course=course).distinct()
                        # group the course_sections_for_course by link_number
                        course_dict[course] = {}
                        for section in course_sections_for_course:
                            if section.link_number in course_dict[course]:
                                course_dict[course][section.link_number].append(section)
                            else:
                                course_dict[course][section.link_number] = [section]
                    
            else:
                error_message = "No results found. Please try again."
        else:
            error_message = "Invalid search parameters. Term is required; Course Subject and Number OR Instructor Name is required."
        
        return render(request, "search/index.html", context={"course_dict": course_dict, "myFilter": myFilter, "error_message": error_message})
    else:
        # if the user has not submitted the form, create an empty filter instance
        myFilter = Course_SectionFilter(request.GET)
        return render(request, "search/index.html", context={"myFilter": myFilter})

def learn_more_view(request):
    return render(request, "search/learn_more.html")

def news_view(request):
    # TODO: get the latest news from the database
    news = News.objects.filter(display=True)
    context = {'news': news}
    return render(request, 'search/news.html', context=context)

# def search(request):
#     if request.method == "POST":
#         form = 
    