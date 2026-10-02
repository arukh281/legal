from django.apps import AppConfig


class ParseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "parse"

    def ready(self) -> None:
        import parse.consumer  # noqa: F401
