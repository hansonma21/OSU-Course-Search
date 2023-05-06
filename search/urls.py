from django.urls import path

from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("search/", views.SearchResultsView.as_view(), name="search_results")
]