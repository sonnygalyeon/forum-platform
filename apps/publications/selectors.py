from apps.publications.models import Publication

def publication_queryset():
    return (
        Publication.objects
        .filter(visibility=Publication.Visibility.PUBLISHED)
        .select_related("author", "community")
        .prefetch_related("tags", "media_links__asset")
    )
