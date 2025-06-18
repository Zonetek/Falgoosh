from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api_applications.accounts"
    verbose_name = "Accounts"

    def ready(self):
        import api_applications.accounts.signals
