from django.urls import path
from django_filters.views import FilterView

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # path("search/", views.SearchResultsView.as_view(), name="search_results")
]