"""
URL configuration for famlyportal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication and accounts
    path('accounts/', include('accounts.urls')),
    
    # Core functionality (coming soon pages, etc.)
    path('', include('core.urls')),
    
    # Main app routes
    path('', RedirectView.as_view(url='/accounts/dashboard/', permanent=False), name='home'),
    path('timesheet/', include('timesheet.urls')),
    path('daycare-invoices/', include('daycare_invoices.urls')),
    path('employment-history/', include('employment_history.urls')),
    path('upcoming-payments/', include('upcoming_payments.urls')),
    path('credit-cards/', include('credit_cards.urls')),
    path('household-budget/', include('household_budget.urls')),
    path('subscription-tracker/', include('subscription_tracker.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
