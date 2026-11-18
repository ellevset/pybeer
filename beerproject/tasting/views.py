from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render

from .forms import VoteForm
from .models import Beer, Vote, Taster, TastingBeer, Tasting

DB = "beer"

def beer_list(request):
    beers = Beer.objects.using(DB)
    return render(request, "tasting/beer_list.html", {"beers": beers})


@login_required
def user_beer_list(request):
    my_vote = Vote.objects.filter(
        beer=OuterRef("pk"), user=request.user
    ).values("score")[:1]

    beers = Beer.objects.annotate(my_score=Subquery(my_vote))
    return render(request, "tasting/beer_list.html", {"beers": beers})


@login_required
def vote_for_beer(request, beer_id):
    beer = get_object_or_404(Beer, pk=beer_id)
    vote, _ = Vote.objects.get_or_create(beer=beer, user=request.user)

    if request.method == "POST":
        form = VoteForm(request.POST, instance=vote)
        if form.is_valid():
            saved_vote = form.save(commit=False)
            saved_vote.beer = beer
            saved_vote.user = request.user
            saved_vote.save()
            return redirect("beer_list")
    else:
        form = VoteForm(instance=vote)

    return render(request, "tasting/vote_form.html", {"beer": beer, "form": form})


@login_required
def my_votes(request):
    votes = Vote.objects.filter(user=request.user).select_related("beer")
    return render(request, "tasting/my_votes.html", {"votes": votes})


def tasting_results(request, tasting_id):
    tasting = get_object_or_404(
        Tasting.objects.using("beer"),
        pk=tasting_id,
    )

    tasting_beers = (
        TastingBeer.objects.using("beer")
        .filter(tasting_id=tasting.pk)
        .select_related("beer")
        .annotate(
            average_score=Avg("votes__score"),
            vote_count=Count("votes"),
        )
        .order_by("position", "beer__name")
    )

    return render(
        request,
        "tasting/tasting_results.html",
        {
            "tasting": tasting,
            "tasting_beers": tasting_beers,
        },
    )

def tasting_detail(request, tasting_id):
    tasting = get_object_or_404(
        Tasting.objects.using(DB),
        pk=tasting_id,
    )

    entries = (
        TastingBeer.objects.using(DB)
        .filter(tasting_id=tasting.pk)
        .select_related("beer")
        .annotate(
            average_score=Avg("votes__score"),
            vote_count=Count("votes"),
        )
        .order_by("position", "beer__name")
    )

    return render(
        request,
        "tasting/tasting_detail.html",
        {"tasting": tasting, "entries": entries},
    )


def tasting_list(request):
    tastings = Tasting.objects.using(DB).order_by("-year", "name")
    return render(request, "tasting/tasting_list.html", {"tastings": tastings})

def taster_list(request):
    tasters = Taster.objects.using(DB).order_by("full_name", "username")
    return render(request, "tasting/taster_list.html", {"tasters": tasters})

def taster_votes(request, taster_id):
    taster = get_object_or_404(
        Taster.objects.using(DB),
        pk=taster_id,
    )

    votes = (
        Vote.objects.using(DB)
        .filter(user_id=taster.pk)
        .select_related("tasting_beer__tasting", "tasting_beer__beer")
        .order_by(
            "-tasting_beer__tasting__year",
            "tasting_beer__position",
        )
    )

    return render(
        request,
        "tasting/taster_votes.html",
        {"taster": taster, "votes": votes},
    )