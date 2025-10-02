"""
Django App Configuration for AI Hub
"""
from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai'
    verbose_name = 'AI & Machine Learning Hub'
    
    def ready(self):
        """
        Import signals and perform app initialization
        """
        # Import signals here when needed
        pass
