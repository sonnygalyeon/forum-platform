from django.db import migrations


FRAMES = [
    dict(slug="iris-line", name="Iris Line", description="Тонкая базовая рамка Night Iris.", tier="base", style_token="iris-line", unlock_type="free", sort_order=10),
    dict(slug="emerald-orbit", name="Emerald Orbit", description="Орбитальная рамка за 50 репутации.", tier="rare", style_token="emerald-orbit", unlock_type="reputation", unlock_value=50, sort_order=20),
    dict(slug="signal-grid", name="Signal Grid", description="Техническая рамка за 150 репутации.", tier="epic", style_token="signal-grid", unlock_type="reputation", unlock_value=150, sort_order=30),
    dict(slug="accepted-halo", name="Accepted Halo", description="Открывается после первого принятого ответа.", tier="epic", style_token="accepted-halo", unlock_type="badge", required_badge_slug="accepted-answer", sort_order=40),
    dict(slug="moderator-arc", name="Moderator Arc", description="Системная рамка команды форума.", tier="staff", style_token="moderator-arc", unlock_type="staff", sort_order=50),
]

BADGES = [
    dict(slug="newcomer", name="Newcomer", description="Аккаунт создан и профиль активен.", tier="base", icon_key="iris", rule_type="always", threshold=0, sort_order=10),
    dict(slug="first-publication", name="First Signal", description="Первая опубликованная запись.", tier="base", icon_key="file", rule_type="publications", threshold=1, sort_order=20),
    dict(slug="first-answer", name="First Answer", description="Первый ответ на вопрос.", tier="base", icon_key="message", rule_type="answers", threshold=1, sort_order=30),
    dict(slug="accepted-answer", name="Accepted", description="Хотя бы один ответ принят автором темы.", tier="rare", icon_key="check", rule_type="accepted", threshold=1, sort_order=40),
    dict(slug="builder", name="Community Builder", description="Создано собственное сообщество.", tier="rare", icon_key="users", rule_type="communities", threshold=1, sort_order=50),
    dict(slug="trusted-100", name="Trusted 100", description="Достигнуто 100 репутации.", tier="epic", icon_key="spark", rule_type="reputation", threshold=100, sort_order=60),
    dict(slug="connected", name="Connected", description="10 подписчиков профиля.", tier="rare", icon_key="link", rule_type="followers", threshold=10, sort_order=70),
    dict(slug="staff", name="Night Iris Staff", description="Участник команды форума.", tier="staff", icon_key="shield", rule_type="staff", threshold=0, sort_order=80),
]


def seed(apps, schema_editor):
    AvatarFrame = apps.get_model("identity", "AvatarFrame")
    Badge = apps.get_model("identity", "Badge")
    for item in FRAMES:
        AvatarFrame.objects.update_or_create(slug=item["slug"], defaults=item)
    for item in BADGES:
        Badge.objects.update_or_create(slug=item["slug"], defaults=item)


def unseed(apps, schema_editor):
    AvatarFrame = apps.get_model("identity", "AvatarFrame")
    Badge = apps.get_model("identity", "Badge")
    AvatarFrame.objects.filter(slug__in=[item["slug"] for item in FRAMES]).delete()
    Badge.objects.filter(slug__in=[item["slug"] for item in BADGES]).delete()


class Migration(migrations.Migration):
    dependencies = [("identity", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
