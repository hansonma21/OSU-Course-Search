from django.urls import path
from django_filters.views import FilterView

from . import views

app_name = "search"

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.learn_more_view, name="learn_more"),
    path("news/", views.news_view, name="news"),
    # path("search/", views.SearchResultsView.as_view(), name="search_results")
]