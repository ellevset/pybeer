
from django.conf import settings
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager


class TasterManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("A username is required.")
        user = self.model(username=username.strip(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class Taster(AbstractBaseUser):
    username = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "username"
    objects = TasterManager()

    def __str__(self):
        return self.username


class Beer(models.Model):
    name = models.CharField(max_length=200)
    brewery = models.CharField(max_length=200, blank=True)
    style = models.CharField(max_length=120, blank=True)
    abv = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True)
    source_url = models.URLField(blank=True)

    class Meta:
        ordering = ["name", "brewery"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "brewery"],
                name="unique_beer_name_brewery",
            )
        ]

    def __str__(self):
        return f"{self.name} — {self.brewery}" if self.brewery else self.name


class Vote(models.Model):
    beer = models.ForeignKey(Beer, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(Taster, on_delete=models.CASCADE, related_name='beer_votes')
    score = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["beer", "user"],
                name="one_vote_per_user_per_beer",
            ),
            models.CheckConstraint(
                condition=models.Q(score__gte=1) & models.Q(score__lte=5),
                name="vote_score_1_to_5",
            ),
        ]

    def __str__(self):
        return f"{self.user} — {self.beer}: {self.score}"
