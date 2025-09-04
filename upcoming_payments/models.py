from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel, FamilyScopedModel, PaymentStatusChoices

User = get_user_model()


def add_months(date, months):
    """Helper function to add months to a date"""
    month = date.month - 1 + months
    year = date.year + month // 12
    month = month % 12 + 1
    day = min(date.day, [31,
        29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date.replace(year=year, month=month, day=day)


class PaymentCategoryManager(models.Manager):
    """Custom manager for PaymentCategory model"""
    
    def active(self):
        """Return active categories"""
        return self.filter(is_active=True)


class PaymentCategory(FamilyScopedModel):
    """Category for organizing payments"""
    name = models.CharField(
        max_length=100,
        help_text="Category name (e.g., Utilities, Insurance, Subscriptions)"
    )
    description = models.TextField(
        blank=True,
        help_text="Category description"
    )
    color = models.CharField(
        max_length=7,
        default='#007bff',
        help_text="Hex color code for UI display"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is active"
    )
    
    objects = PaymentCategoryManager()
    
    class Meta:
        unique_together = ['family', 'name']
        ordering = ['name']
        verbose_name = 'Payment Category'
        verbose_name_plural = 'Payment Categories'
    
    def __str__(self):
        return self.name


class RecurringPaymentManager(models.Manager):
    """Custom manager for RecurringPayment model"""
    
    def active(self):
        """Return active recurring payments"""
        return self.filter(is_active=True)
    
    def due_soon(self, days=7):
        """Return payments due within specified days"""
        cutoff_date = timezone.now().date() + timezone.timedelta(days=days)
        return self.filter(
            is_active=True,
            next_due_date__lte=cutoff_date
        )
    
    def by_category(self, category):
        """Return payments by category"""
        return self.filter(category=category)


class RecurringPayment(FamilyScopedModel):
    """Recurring payment setup"""
    
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semiannually', 'Semi-annually'),
        ('annually', 'Annually'),
    ]
    
    REMINDER_CHOICES = [
        (1, '1 day before'),
        (3, '3 days before'),
        (7, '1 week before'),
        (14, '2 weeks before'),
        (30, '1 month before'),
    ]
    
    payee = models.CharField(
        max_length=200,
        help_text="Who the payment is made to"
    )
    description = models.CharField(
        max_length=200,
        help_text="Payment description"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount"
    )
    category = models.ForeignKey(
        PaymentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Payment category"
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='monthly',
        help_text="How often this payment occurs"
    )
    start_date = models.DateField(
        default=timezone.now,
        help_text="When this recurring payment starts"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="When this recurring payment ends (optional)"
    )
    next_due_date = models.DateField(
        help_text="Next payment due date"
    )
    auto_pay = models.BooleanField(
        default=False,
        help_text="Whether this payment is on auto-pay"
    )
    reminder_days = models.PositiveIntegerField(
        choices=REMINDER_CHOICES,
        default=3,
        help_text="Days before due date to send reminder"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this recurring payment is active"
    )
    account_info = models.CharField(
        max_length=200,
        blank=True,
        help_text="Account or reference number"
    )
    
    objects = RecurringPaymentManager()
    
    class Meta:
        ordering = ['next_due_date', 'payee']
        verbose_name = 'Recurring Payment'
        verbose_name_plural = 'Recurring Payments'
    
    def __str__(self):
        return f"{self.payee} - ${self.amount} ({dict(self.FREQUENCY_CHOICES)[self.frequency]})"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        
        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")
        
        if self.next_due_date < self.start_date:
            raise ValidationError("Next due date cannot be before start date.")
    
    def calculate_next_due_date(self, from_date=None):
        """Calculate the next due date based on frequency"""
        if from_date is None:
            from_date = self.next_due_date
        
        if self.frequency == 'weekly':
            return from_date + timezone.timedelta(weeks=1)
        elif self.frequency == 'biweekly':
            return from_date + timezone.timedelta(weeks=2)
        elif self.frequency == 'monthly':
            return add_months(from_date, 1)
        elif self.frequency == 'quarterly':
            return add_months(from_date, 3)
        elif self.frequency == 'semiannually':
            return add_months(from_date, 6)
        elif self.frequency == 'annually':
            return add_months(from_date, 12)
        else:
            return add_months(from_date, 1)  # Default to monthly
    
    def update_next_due_date(self):
        """Update next due date and save"""
        self.next_due_date = self.calculate_next_due_date()
        self.save(update_fields=['next_due_date'])
    
    @property
    def is_due_soon(self):
        """Check if payment is due within reminder period"""
        reminder_date = timezone.now().date() + timezone.timedelta(days=self.reminder_days)
        return self.next_due_date <= reminder_date
    
    @property
    def is_overdue(self):
        """Check if payment is overdue"""
        return self.next_due_date < timezone.now().date()
    
    @property
    def annual_amount(self):
        """Calculate annual payment amount"""
        if self.frequency == 'weekly':
            return self.amount * 52
        elif self.frequency == 'biweekly':
            return self.amount * 26
        elif self.frequency == 'monthly':
            return self.amount * 12
        elif self.frequency == 'quarterly':
            return self.amount * 4
        elif self.frequency == 'semiannually':
            return self.amount * 2
        elif self.frequency == 'annually':
            return self.amount
        else:
            return self.amount * 12  # Default to monthly


class PaymentInstanceManager(models.Manager):
    """Custom manager for PaymentInstance model"""
    
    def for_month(self, year, month):
        """Return payment instances for a specific month"""
        return self.filter(
            due_date__year=year,
            due_date__month=month
        )
    
    def pending(self):
        """Return pending payment instances"""
        return self.filter(status='pending')
    
    def paid(self):
        """Return paid payment instances"""
        return self.filter(status='paid')
    
    def overdue(self):
        """Return overdue payment instances"""
        return self.filter(
            status='pending',
            due_date__lt=timezone.now().date()
        )


class PaymentInstance(FamilyScopedModel):
    """Individual payment instance from recurring payment"""
    recurring_payment = models.ForeignKey(
        RecurringPayment,
        on_delete=models.CASCADE,
        help_text="The recurring payment this instance belongs to"
    )
    due_date = models.DateField(
        help_text="Date this payment is due"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount (can differ from recurring amount)"
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatusChoices.choices,
        default=PaymentStatusChoices.PENDING,
        help_text="Payment status"
    )
    paid_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date payment was made"
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual amount paid"
    )
    confirmation_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Payment confirmation number"
    )
    notes = models.TextField(
        blank=True,
        help_text="Payment notes"
    )
    reminder_sent = models.BooleanField(
        default=False,
        help_text="Whether reminder has been sent"
    )
    
    objects = PaymentInstanceManager()
    
    class Meta:
        unique_together = ['recurring_payment', 'due_date']
        ordering = ['due_date']
        verbose_name = 'Payment Instance'
        verbose_name_plural = 'Payment Instances'
    
    def __str__(self):
        return f"{self.recurring_payment.payee} - {self.due_date} (${self.amount})"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        
        if self.paid_date and self.paid_date > timezone.now().date():
            raise ValidationError("Paid date cannot be in the future.")
        
        if self.status == 'paid' and not self.paid_date:
            raise ValidationError("Paid date is required when status is paid.")
        
        if self.paid_amount is not None and self.paid_amount < 0:
            raise ValidationError("Paid amount cannot be negative.")
    
    def mark_as_paid(self, paid_date=None, paid_amount=None, confirmation_number=''):
        """Mark payment instance as paid"""
        self.status = PaymentStatusChoices.PAID
        self.paid_date = paid_date or timezone.now().date()
        self.paid_amount = paid_amount or self.amount
        self.confirmation_number = confirmation_number
        self.save()
    
    def mark_as_failed(self, notes=''):
        """Mark payment instance as failed"""
        self.status = 'failed'
        if notes:
            self.notes = f"{self.notes}\n{notes}" if self.notes else notes
        self.save()
    
    @property
    def is_overdue(self):
        """Check if payment instance is overdue"""
        return (
            self.status == 'pending' and 
            self.due_date < timezone.now().date()
        )
    
    @property
    def days_until_due(self):
        """Calculate days until due (negative if overdue)"""
        delta = self.due_date - timezone.now().date()
        return delta.days


class PaymentReminder(FamilyScopedModel):
    """Payment reminder tracking"""
    payment_instance = models.ForeignKey(
        PaymentInstance,
        on_delete=models.CASCADE,
        help_text="Payment instance this reminder is for"
    )
    reminder_date = models.DateField(
        help_text="Date reminder should be sent"
    )
    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When reminder was actually sent"
    )
    email_sent = models.BooleanField(
        default=False,
        help_text="Whether email reminder was sent"
    )
    push_sent = models.BooleanField(
        default=False,
        help_text="Whether push notification was sent"
    )
    
    class Meta:
        ordering = ['reminder_date']
        verbose_name = 'Payment Reminder'
        verbose_name_plural = 'Payment Reminders'
    
    def __str__(self):
        return f"Reminder for {self.payment_instance} on {self.reminder_date}"
    
    def mark_as_sent(self, email=True, push=False):
        """Mark reminder as sent"""
        self.sent_date = timezone.now()
        self.email_sent = email
        self.push_sent = push
        self.save()
