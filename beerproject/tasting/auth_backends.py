from django.contrib.auth.backends import BaseBackend
from .models import Taster


class TasterBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or password is None:
            return None

        try:
            user = Taster.objects.get(username=username)
        except Taster.DoesNotExist:
            return None

        if user.is_active and user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return Taster.objects.get(pk=user_id, is_active=True)
        except Taster.DoesNotExist:
            return None
