"""
Subscription Tracker Models

Comprehensive models for tracking family subscription services,
renewal dates, costs, and integration with budget management.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from decimal import Decimal
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

User = get_user_model()


class SubscriptionCategory(models.Model):
    """Categories for organizing subscriptions"""
    
    family = models.ForeignKey('accounts.Family', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#007bff', help_text='Hex color code')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "subscription categories"
        unique_together = ['family', 'name']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.family.name} - {self.name}"
    
    def subscription_count(self):
        """Count active subscriptions in this category"""
        return self.subscriptions.filter(status='active').count()
    
    def total_monthly_cost(self):
        """Calculate total monthly cost for this category"""
        total = Decimal('0.00')
        for subscription in self.subscriptions.filter(status='active'):
            total += subscription.monthly_cost()
        return total


class SubscriptionService(models.Model):
    """Individual subscription services"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('biannually', 'Bi-annually'),
        ('annually', 'Annually'),
        ('weekly', 'Weekly'),
        ('custom', 'Custom'),
    ]
    
    # Basic Information
    family = models.ForeignKey('accounts.Family', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(SubscriptionCategory, on_delete=models.SET_NULL, 
                                null=True, blank=True, related_name='subscriptions')
    
    # Cost Information
    cost = models.DecimalField(max_digits=10, decimal_places=2, 
                              validators=[MinValueValidator(Decimal('0.01'))])
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, 
                                   default='monthly')
    
    # Dates
    start_date = models.DateField()
    next_billing_date = models.DateField()
    
    # Additional Information
    website_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Management
    auto_renew = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=100, blank=True, 
                                    help_text='Credit card or payment method used')
    
    # Tracking
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, 
                               related_name='added_subscriptions')
    used_by = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, 
                                   related_name='used_subscriptions',
                                   help_text='Family members who use this subscription')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['family', 'name']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.family.name} - {self.name}"
    
    def get_absolute_url(self):
        return reverse('subscription_tracker:subscription_detail', kwargs={'pk': self.pk})
    
    def monthly_cost(self):
        """Convert cost to monthly equivalent"""
        if self.billing_cycle == 'monthly':
            return self.cost
        elif self.billing_cycle == 'quarterly':
            return self.cost / Decimal('3')
        elif self.billing_cycle == 'biannually':
            return self.cost / Decimal('6')
        elif self.billing_cycle == 'annually':
            return self.cost / Decimal('12')
        elif self.billing_cycle == 'weekly':
            return self.cost * Decimal('4.33')  # Average weeks per month
        else:  # custom
            return self.cost
    
    def annual_cost(self):
        """Convert cost to annual equivalent"""
        return self.monthly_cost() * Decimal('12')
    
    def days_until_renewal(self):
        """Calculate days until next billing"""
        from datetime import date
        return (self.next_billing_date - date.today()).days
    
    def is_due_soon(self, days=7):
        """Check if renewal is due within specified days"""
        return 0 <= self.days_until_renewal() <= days
    
    def calculate_next_billing_date(self):
        """Calculate next billing date based on current date and cycle"""
        if self.billing_cycle == 'monthly':
            return self.next_billing_date + relativedelta(months=1)
        elif self.billing_cycle == 'quarterly':
            return self.next_billing_date + relativedelta(months=3)
        elif self.billing_cycle == 'biannually':
            return self.next_billing_date + relativedelta(months=6)
        elif self.billing_cycle == 'annually':
            return self.next_billing_date + relativedelta(years=1)
        elif self.billing_cycle == 'weekly':
            return self.next_billing_date + timedelta(weeks=1)
        else:
            return self.next_billing_date
    
    def mark_payment_made(self):
        """Mark payment as made and update next billing date"""
        self.next_billing_date = self.calculate_next_billing_date()
        self.save()
        
        # Create payment record
        PaymentRecord.objects.create(
            subscription=self,
            amount=self.cost,
            payment_date=datetime.now().date(),
            payment_method=self.payment_method
        )
    
    def pause(self):
        """Pause the subscription"""
        self.status = 'paused'
        self.save()
    
    def resume(self):
        """Resume a paused subscription"""
        if self.status == 'paused':
            self.status = 'active'
            # Update next billing date to account for pause period
            self.next_billing_date = datetime.now().date() + timedelta(days=30)
            self.save()
    
    def cancel(self):
        """Cancel the subscription"""
        self.status = 'cancelled'
        self.cancelled_date = datetime.now()
        self.save()


class PaymentRecord(models.Model):
    """Track payment history for subscriptions"""
    
    subscription = models.ForeignKey(SubscriptionService, on_delete=models.CASCADE,
                                   related_name='payment_history')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.subscription.name} - ${self.amount} on {self.payment_date}"


class SubscriptionAlert(models.Model):
    """Alerts and notifications for subscriptions"""
    
    ALERT_TYPE_CHOICES = [
        ('renewal_due', 'Renewal Due'),
        ('price_change', 'Price Change'),
        ('payment_failed', 'Payment Failed'),
        ('duplicate_service', 'Duplicate Service'),
        ('unused_service', 'Unused Service'),
        ('savings_opportunity', 'Savings Opportunity'),
    ]
    
    family = models.ForeignKey('accounts.Family', on_delete=models.CASCADE)
    subscription = models.ForeignKey(SubscriptionService, on_delete=models.CASCADE,
                                   related_name='alerts', null=True, blank=True)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.family.name} - {self.title}"


class SubscriptionUsageLog(models.Model):
    """Track subscription usage by family members"""
    
    subscription = models.ForeignKey(SubscriptionService, on_delete=models.CASCADE,
                                   related_name='usage_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    used_date = models.DateField(auto_now_add=True)
    usage_notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['subscription', 'user', 'used_date']
        ordering = ['-used_date']
    
    def __str__(self):
        return f"{self.user.username} used {self.subscription.name} on {self.used_date}"
