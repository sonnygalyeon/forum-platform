from rest_framework import serializers

from apps.communities.api.serializers import CommunitySerializer
from apps.publications.api.serializers import PublicationListSerializer
from apps.users.api.serializers import UserProfileSerializer


class SearchTagSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    publication_count = serializers.IntegerField(min_value=0)


class SearchCountsSerializer(serializers.Serializer):
    publications = serializers.IntegerField(min_value=0)
    users = serializers.IntegerField(min_value=0)
    communities = serializers.IntegerField(min_value=0)
    tags = serializers.IntegerField(min_value=0)


class SearchPageQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, max_value=2147483647, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=50, required=False)


class SearchPaginationSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1)
    page_size = serializers.IntegerField(min_value=1, max_value=50)
    total_pages = serializers.IntegerField(min_value=1)
    total_results = serializers.IntegerField(min_value=0)
    has_next = serializers.BooleanField()
    has_previous = serializers.BooleanField()


class SearchResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    scope = serializers.CharField()
    counts = SearchCountsSerializer()
    publications = PublicationListSerializer(many=True)
    users = UserProfileSerializer(many=True)
    communities = CommunitySerializer(many=True)
    tags = SearchTagSerializer(many=True)
    pagination = SearchPaginationSerializer(required=False, allow_null=True)


class DiscoveryResponseSerializer(serializers.Serializer):
    personalized = serializers.BooleanField()
    recommended_publications = PublicationListSerializer(many=True)
    popular_tags = SearchTagSerializer(many=True)
    active_communities = CommunitySerializer(many=True)
    open_topics = PublicationListSerializer(many=True)
    top_users = UserProfileSerializer(many=True)
