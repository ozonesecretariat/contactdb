from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from two_factor.utils import default_device

from common.citext import CICharField, CIEmailField


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, email):
        return self.get(email=email)

    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")

        if not password:
            raise ValueError("Users must have a password.")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self.create_user(email, password, **extra_fields)
        user.is_superuser = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = CIEmailField(unique=True)
    first_name = CICharField(max_length=250, null=True, blank=True)
    last_name = CICharField(max_length=250, null=True, blank=True)

    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
        help_text="Designates whether the account can be used. It is recommended to disable an "
        "account instead of deleting.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"

    objects = UserManager()

    def __str__(self):
        return self.email

    def natural_key(self):
        return (self.email,)

    @property
    def two_factor_enabled(self):
        return bool(default_device(self))

    @property
    def is_staff(self):
        return True
