from django.apps import AppConfig

class ExcelUploaderConfig(AppConfig):
    """
    Configuration class for the 'excel_uploader' Django application.

    This class is automatically detected by Django when the application is
    added to INSTALLED_APPS. It allows for application-specific configuration.
    """
    default_auto_field = 'django.db.models.BigAutoField' # Standard setting for primary key type.
    name = 'excel_uploader' # The name of the application.
