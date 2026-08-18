import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("communities", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CommunitySubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("community", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="subscriptions", to="communities.community")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="community_subscriptions", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="UserFollow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("follower", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="following_edges", to=settings.AUTH_USER_MODEL)),
                ("following", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="follower_edges", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="communitysubscription",
            constraint=models.UniqueConstraint(fields=("user", "community"), name="social_unique_community_subscription"),
        ),
        migrations.AddIndex(
            model_name="communitysubscription",
            index=models.Index(fields=["user", "-created_at"], name="social_comm_user_id_917f52_idx"),
        ),
        migrations.AddIndex(
            model_name="communitysubscription",
            index=models.Index(fields=["community", "-created_at"], name="social_comm_communi_2d04e8_idx"),
        ),
        migrations.AddConstraint(
            model_name="userfollow",
            constraint=models.UniqueConstraint(fields=("follower", "following"), name="social_unique_user_follow"),
        ),
        migrations.AddConstraint(
            model_name="userfollow",
            constraint=models.CheckConstraint(condition=~models.Q(follower=models.F("following")), name="social_user_cannot_follow_self"),
        ),
        migrations.AddIndex(
            model_name="userfollow",
            index=models.Index(fields=["follower", "-created_at"], name="social_user_followe_0bada7_idx"),
        ),
        migrations.AddIndex(
            model_name="userfollow",
            index=models.Index(fields=["following", "-created_at"], name="social_user_followi_535fb2_idx"),
        ),
    ]
