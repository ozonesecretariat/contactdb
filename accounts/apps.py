from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "accounts"
    verbose_name = "Accounts"

    def ready(self):
        import accounts.tasks  # noqa
