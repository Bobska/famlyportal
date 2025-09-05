from django.apps import AppConfig


class SubscriptionTrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscription_tracker'
    verbose_name = 'Subscription Tracker'
    
    def ready(self):
        """Initialize app configuration"""
        # Import signal handlers if needed
        pass
