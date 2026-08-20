from django.db import transaction
from apps.communities.models import Community

@transaction.atomic
def create_community(*, owner, slug, name, description=""):
    community = Community.objects.create(owner=owner, slug=slug.strip().lower(), name=name.strip(), description=description.strip())
    from apps.identity.services import sync_identity_state
    sync_identity_state(owner)
    return community
