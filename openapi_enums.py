"""Stable enum choice sets used only for OpenAPI component naming.

Keep these values in sync with the corresponding Django model choices.
This module intentionally has no Django imports so drf-spectacular can import
it safely while settings are being loaded.
"""

PUBLICATION_KIND_CHOICES = [
    ("post", "Post"),
    ("article", "Article"),
    ("topic", "Topic"),
]

COMMENT_KIND_CHOICES = [
    ("answer", "Answer"),
    ("comment", "Comment"),
    ("reply", "Reply"),
]

MEDIA_ASSET_KIND_CHOICES = [
    ("image", "Image"),
    ("video", "Video"),
    ("file", "File"),
]

NOTIFICATION_KIND_CHOICES = [
    ("new_publication", "New publication"),
    ("publication_response", "Publication response"),
    ("comment_reply", "Comment reply"),
    ("answer_accepted", "Answer accepted"),
    ("new_follower", "New follower"),
    ("moderation_update", "Moderation update"),
]

MEDIA_ASSET_STATUS_CHOICES = [
    ("uploading", "Uploading"),
    ("pending_scan", "Pending scan"),
    ("ready", "Ready"),
    ("aborted", "Aborted"),
    ("rejected", "Rejected"),
]

NOTIFICATION_EVENT_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("done", "Done"),
    ("failed", "Failed"),
]

REPORT_STATUS_CHOICES = [
    ("open", "Open"),
    ("reviewing", "Reviewing"),
    ("resolved", "Resolved"),
    ("dismissed", "Dismissed"),
]

REPORT_TARGET_TYPE_CHOICES = [
    ("publication", "Publication"),
    ("comment", "Comment"),
    ("user", "User"),
]

MODERATION_ACTION_TARGET_TYPE_CHOICES = [
    ("publication", "Publication"),
    ("comment", "Comment"),
]

IDENTITY_TIER_CHOICES = [
    ("base", "Base"),
    ("rare", "Rare"),
    ("epic", "Epic"),
    ("legendary", "Legendary"),
    ("staff", "Staff"),
]

IDENTITY_ACCENT_CHOICES = [
    ("emerald", "Emerald"),
    ("jade", "Jade"),
    ("ice", "Ice"),
    ("violet", "Violet"),
]

IDENTITY_FRAME_UNLOCK_CHOICES = [
    ("free", "Free"),
    ("reputation", "Reputation"),
    ("badge", "Badge"),
    ("staff", "Staff"),
]

IDENTITY_BADGE_RULE_CHOICES = [
    ("always", "Always"),
    ("reputation", "Reputation"),
    ("publications", "Publications"),
    ("answers", "Answers"),
    ("accepted", "Accepted answers"),
    ("followers", "Followers"),
    ("communities", "Owned communities"),
    ("staff", "Staff"),
]

MESSENGER_CONVERSATION_KIND_CHOICES = [
    ("direct", "Direct"),
    ("group", "Group"),
]

MESSENGER_MEMBER_ROLE_CHOICES = [
    ("owner", "Owner"),
    ("admin", "Admin"),
    ("member", "Member"),
]

COMMUNITY_STAFF_ROLE_CHOICES = [
    ("moderator", "Moderator"),
    ("editor", "Editor"),
]

MESSENGER_CHAT_THEME_CHOICES = [
    ("iris", "Iris"),
    ("ocean", "Ocean"),
    ("violet", "Violet"),
    ("amber", "Amber"),
    ("rose", "Rose"),
    ("mono", "Mono"),
]

MESSENGER_WALLPAPER_CHOICES = [
    ("iris-grid", "Iris Grid"),
    ("midnight", "Midnight"),
    ("aurora", "Aurora"),
    ("paper", "Paper"),
    ("graphite", "Graphite"),
    ("none", "None"),
    ("custom", "Custom"),
]

MESSENGER_MESSAGE_SCALE_CHOICES = [
    ("small", "Small"),
    ("normal", "Normal"),
    ("large", "Large"),
]

MESSENGER_PRIVACY_CHOICES = [
    ("everyone", "Everyone"),
    ("following", "Following"),
    ("nobody", "Nobody"),
]
