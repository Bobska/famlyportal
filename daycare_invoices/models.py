from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import FamilyScopedModel, PaymentStatusChoices, PaymentMethodChoices

User = get_user_model()


class DaycareProviderManager(models.Manager):
    """Custom manager for DaycareProvider model"""
    
    def active(self):
        """Return only active providers"""
        return self.filter(is_active=True)


class DaycareProvider(FamilyScopedModel):
    """Daycare provider/center model"""
    name = models.CharField(
        max_length=200,
        help_text="Name of the daycare provider"
    )
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        help_text="Main contact person at the daycare"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Contact phone number"
    )
    email = models.EmailField(
        blank=True,
        help_text="Contact email address"
    )
    address = models.TextField(
        blank=True,
        help_text="Physical address of the daycare"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this provider is currently active"
    )
    license_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Daycare license number"
    )
    
    objects = DaycareProviderManager()
    
    class Meta:
        ordering = ['name']
        unique_together = ['family', 'name']
        verbose_name = 'Daycare Provider'
        verbose_name_plural = 'Daycare Providers'
    
    def __str__(self):
        return f"{self.name} ({self.family.name})"


class Child(FamilyScopedModel):
    """Child model for daycare tracking"""
    first_name = models.CharField(
        max_length=50,
        help_text="Child's first name"
    )
    last_name = models.CharField(
        max_length=50,
        help_text="Child's last name"
    )
    date_of_birth = models.DateField(
        help_text="Child's date of birth"
    )
    provider = models.ForeignKey(
        DaycareProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Current daycare provider"
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date child started at current provider"
    )
    is_enrolled = models.BooleanField(
        default=True,
        help_text="Whether child is currently enrolled"
    )
    special_needs = models.TextField(
        blank=True,
        help_text="Any special needs or requirements"
    )
    emergency_contact = models.CharField(
        max_length=100,
        blank=True,
        help_text="Emergency contact person"
    )
    emergency_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Emergency contact phone number"
    )
    
    class Meta:
        ordering = ['first_name', 'last_name']
        unique_together = ['family', 'first_name', 'last_name']
        verbose_name = 'Child'
        verbose_name_plural = 'Children'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        if self.date_of_birth and self.date_of_birth > timezone.now().date():
            raise ValidationError("Date of birth cannot be in the future.")
        
        if (self.start_date and self.date_of_birth and 
            self.start_date < self.date_of_birth):
            raise ValidationError("Start date cannot be before date of birth.")
    
    @property
    def full_name(self):
        """Get child's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate child's age in years"""
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class InvoiceManager(models.Manager):
    """Custom manager for Invoice model"""
    
    def overdue(self):
        """Return overdue invoices"""
        return self.filter(
            due_date__lt=timezone.now().date(),
            status__in=[PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL]
        )
    
    def for_child(self, child):
        """Return invoices for a specific child"""
        return self.filter(child=child)
    
    def for_provider(self, provider):
        """Return invoices for a specific provider"""
        return self.filter(provider=provider)


class Invoice(FamilyScopedModel):
    """Invoice model for daycare billing"""
    provider = models.ForeignKey(
        DaycareProvider,
        on_delete=models.CASCADE,
        help_text="Daycare provider who issued the invoice"
    )
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        help_text="Child this invoice is for"
    )
    invoice_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Provider's invoice number"
    )
    invoice_date = models.DateField(
        default=timezone.now,
        help_text="Date the invoice was issued"
    )
    due_date = models.DateField(
        help_text="Date payment is due"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Invoice amount"
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatusChoices.choices,
        default=PaymentStatusChoices.PENDING,
        help_text="Payment status of the invoice"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of services or period covered"
    )
    services_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Start date of services covered by this invoice"
    )
    services_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date of services covered by this invoice"
    )
    
    objects = InvoiceManager()
    
    class Meta:
        ordering = ['-invoice_date']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
    
    def __str__(self):
        return f"Invoice {self.invoice_number or self.pk} - {self.child.full_name} - ${self.amount}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.amount < 0:
            raise ValidationError("Invoice amount cannot be negative.")
        
        if self.due_date < self.invoice_date:
            raise ValidationError("Due date cannot be before invoice date.")
        
        if (self.services_start_date and self.services_end_date and
            self.services_start_date > self.services_end_date):
            raise ValidationError("Services start date cannot be after end date.")
        
        # Ensure child belongs to same family as provider
        if (self.child and self.provider and 
            self.child.family != self.provider.family):
            raise ValidationError("Child and provider must belong to the same family.")
    
    @property
    def total_payments(self):
        """Calculate total payments made against this invoice"""
        return sum(payment.amount for payment in self.payment_set.all())
    
    @property
    def remaining_balance(self):
        """Calculate remaining balance on the invoice"""
        return self.amount - self.total_payments
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        return (self.due_date < timezone.now().date() and 
                self.status in [PaymentStatusChoices.PENDING, PaymentStatusChoices.PARTIAL])
    
    def update_status(self):
        """Update invoice status based on payments"""
        total_paid = self.total_payments
        
        if total_paid >= self.amount:
            self.status = PaymentStatusChoices.PAID
        elif total_paid > 0:
            self.status = PaymentStatusChoices.PARTIAL
        elif self.is_overdue:
            self.status = PaymentStatusChoices.OVERDUE
        else:
            self.status = PaymentStatusChoices.PENDING
        
        self.save()


class Payment(FamilyScopedModel):
    """Payment model for tracking invoice payments"""
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        help_text="Invoice this payment is for"
    )
    payment_date = models.DateField(
        default=timezone.now,
        help_text="Date payment was made"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount"
    )
    method = models.CharField(
        max_length=20,
        choices=PaymentMethodChoices.choices,
        default=PaymentMethodChoices.CASH,
        help_text="Payment method used"
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Check number, transaction ID, etc."
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the payment"
    )
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"Payment ${self.amount} for {self.invoice}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.amount <= 0:
            raise ValidationError("Payment amount must be positive.")
        
        if self.payment_date > timezone.now().date():
            raise ValidationError("Payment date cannot be in the future.")
    
    def save(self, *args, **kwargs):
        """Override save to update invoice status and family"""
        if self.invoice:
            self.family = self.invoice.family
        super().save(*args, **kwargs)
        
        # Update invoice status after saving payment
        if self.invoice:
            self.invoice.update_status()
