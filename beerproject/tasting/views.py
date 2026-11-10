from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect, render

from .forms import VoteForm
from .models import Beer, Vote


@login_required
def beer_list(request):
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
