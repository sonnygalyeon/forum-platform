from django.urls import path

from apps.discovery.api.views import DiscoveryView, SearchView


urlpatterns = [
    path("search/", SearchView.as_view(), name="search"),
    path("discover/", DiscoveryView.as_view(), name="discover"),
]
