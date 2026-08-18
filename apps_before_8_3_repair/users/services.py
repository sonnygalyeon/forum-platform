from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models import User

@transaction.atomic
def register_user(*, nickname, email, password, first_name, last_name, country, nationality, interface_language):
    return User.objects.create_user(
        nickname=nickname, email=email, password=password, first_name=first_name, last_name=last_name,
        country=country, nationality=nationality, interface_language=interface_language,
    )

def create_token_pair(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}
