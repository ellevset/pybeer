
from django.urls import path

from . import views

app_name= "tasting"

urlpatterns = [
    path("", views.beer_list, name="beer_list"),
    path("beer/<int:beer_id>/vote/", views.vote_for_beer, name="vote_for_beer"),
    path("my-votes/", views.my_votes, name="my_votes"),
    path("tastings/<int:tasting_id>/", views.tasting_results, name="results"),
    path("tastings/<int:tasting_id>/", views.tasting_detail, name="tasting-detail"),
    path("tasters/", views.taster_list, name="taster-list"),
    path("tasters/<int:taster_id>/votes/", views.taster_votes, name="taster-votes"),
]
