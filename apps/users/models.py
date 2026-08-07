import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(
        self,
        nickname,
        email,
        password=None,
        **extra_fields,
    ):
        if not nickname:
            raise ValueError("Nickname is required")

        if not email:
            raise ValueError("Email is required")

        nickname = nickname.strip()
        email = self.normalize_email(email)

        user = self.model(
            nickname=nickname,
            email=email,
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        nickname,
        email,
        password=None,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(
            nickname=nickname,
            email=email,
            password=password,
            **extra_fields,
        )


class User(AbstractUser):
    username = None

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    nickname = models.CharField(
        max_length=32,
        unique=True,
    )

    email = models.EmailField(
        unique=True,
    )

    country = models.CharField(
        max_length=2,
    )

    nationality = models.CharField(
        max_length=2,
    )

    interface_language = models.CharField(
        max_length=10,
        default="en",
    )

    bio = models.TextField(
        max_length=1000,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    USERNAME_FIELD = "nickname"

    REQUIRED_FIELDS = [
        "email",
        "first_name",
        "last_name",
        "country",
        "nationality",
    ]

    objects = UserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("nickname"),
                name="users_nickname_case_insensitive_unique",
            ),
        ]

    def __str__(self):
        return self.nickname