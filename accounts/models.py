from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from two_factor.utils import default_device

from contactdb.citext import CIEmailField


class UserManager(BaseUserManager):
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
        user.is_staff = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = CIEmailField(
        unique=True,
        help_text="You can use <a href=\"../password/\">this form</a> to change the password. "
                  "It is recommended to use 'Forgot password' for account retrieval.",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active",
        help_text="Designates whether the account can be used. It is recommended to disable an "
                  "account instead of deleting.",
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name="Staff",
        help_text="Designates whether the user can access the admin page.",
    )
    can_view = models.BooleanField(
        default=True,
        verbose_name="View contacts",
        help_text="Designates whether the user can view contacts.",
    )
    can_edit = models.BooleanField(
        default=False,
        verbose_name="Edit contacts",
        help_text="Designates whether the user can edit contacts.",
    )
    can_import = models.BooleanField(
        default=False,
        verbose_name="Import contacts",
        help_text="Designates whether the user can import contacts.",
    )
    can_send_mail = models.BooleanField(
        default=False,
        verbose_name="Send emails",
        help_text="Designates whether the user can send emails to contacts.",
    )

    USERNAME_FIELD = "email"

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def two_factor_enabled(self):
        return bool(default_device(self))
