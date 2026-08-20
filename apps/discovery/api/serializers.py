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


class SearchResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    scope = serializers.CharField()
    counts = SearchCountsSerializer()
    publications = PublicationListSerializer(many=True)
    users = UserProfileSerializer(many=True)
    communities = CommunitySerializer(many=True)
    tags = SearchTagSerializer(many=True)


class DiscoveryResponseSerializer(serializers.Serializer):
    popular_tags = SearchTagSerializer(many=True)
    active_communities = CommunitySerializer(many=True)
    open_topics = PublicationListSerializer(many=True)
    top_users = UserProfileSerializer(many=True)
