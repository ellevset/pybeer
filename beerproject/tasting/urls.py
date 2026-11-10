from django.urls import path
from . import views

urlpatterns = [
    path("", views.beer_list, name="beer_list"),
    path("beer/<int:beer_id>/vote/", views.vote_for_beer, name="vote_for_beer"),
    path("my-votes/", views.my_votes, name="my_votes"),
]
