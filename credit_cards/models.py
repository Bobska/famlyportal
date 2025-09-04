from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel, FamilyScopedModel

User = get_user_model()


class CreditCardManager(models.Manager):
    """Custom manager for CreditCard model"""
    
    def active(self):
        """Return active credit cards"""
        return self.filter(is_active=True)
    
    def expired(self):
        """Return expired credit cards"""
        today = timezone.now().date()
        return self.filter(
            expiry_month__lt=today.month,
            expiry_year__lte=today.year
        ).union(
            self.filter(expiry_year__lt=today.year)
        )
    
    def expiring_soon(self, months=3):
        """Return cards expiring within specified months"""
        today = timezone.now().date()
        future_date = today.replace(year=today.year + (today.month + months - 1) // 12,
                                   month=(today.month + months - 1) % 12 + 1)
        
        return self.filter(
            expiry_year__lt=future_date.year
        ).union(
            self.filter(
                expiry_year=future_date.year,
                expiry_month__lte=future_date.month
            )
        )


class CreditCard(FamilyScopedModel):
    """Credit card model for tracking cards and their details"""
    
    CARD_TYPE_CHOICES = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
        ('other', 'Other'),
    ]
    
    nickname = models.CharField(
        max_length=100,
        help_text="Nickname for the card (e.g., 'Main Visa', 'Business Card')"
    )
    card_type = models.CharField(
        max_length=20,
        choices=CARD_TYPE_CHOICES,
        help_text="Type of credit card"
    )
    last_four_digits = models.CharField(
        max_length=4,
        help_text="Last 4 digits of card number"
    )
    expiry_month = models.PositiveIntegerField(
        help_text="Expiry month (1-12)"
    )
    expiry_year = models.PositiveIntegerField(
        help_text="Expiry year (YYYY)"
    )
    credit_limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Credit limit for this card"
    )
    current_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current balance on the card"
    )
    available_credit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Available credit (auto-calculated)"
    )
    minimum_payment = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Current minimum payment due"
    )
    statement_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Last statement balance"
    )
    statement_date = models.DateField(
        null=True,
        blank=True,
        help_text="Last statement date"
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Payment due date"
    )
    apr = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual Percentage Rate"
    )
    annual_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Annual fee for this card"
    )
    rewards_program = models.CharField(
        max_length=200,
        blank=True,
        help_text="Rewards program details"
    )
    issuer = models.CharField(
        max_length=100,
        help_text="Card issuing bank/company"
    )
    account_holder = models.CharField(
        max_length=100,
        help_text="Name on the card"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about this card"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this card is active"
    )
    
    objects = CreditCardManager()
    
    class Meta:
        ordering = ['nickname']
        verbose_name = 'Credit Card'
        verbose_name_plural = 'Credit Cards'
    
    def __str__(self):
        return f"{self.nickname} (*{self.last_four_digits})"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if len(self.last_four_digits) != 4 or not self.last_four_digits.isdigit():
            raise ValidationError("Last four digits must be exactly 4 digits.")
        
        if not (1 <= self.expiry_month <= 12):
            raise ValidationError("Expiry month must be between 1 and 12.")
        
        current_year = timezone.now().year
        if self.expiry_year < current_year:
            raise ValidationError("Expiry year cannot be in the past.")
        
        if self.credit_limit <= 0:
            raise ValidationError("Credit limit must be greater than zero.")
        
        if self.current_balance < 0:
            raise ValidationError("Current balance cannot be negative.")
        
        if self.current_balance > self.credit_limit:
            raise ValidationError("Current balance cannot exceed credit limit.")
        
        if self.apr is not None and (self.apr < 0 or self.apr > 100):
            raise ValidationError("APR must be between 0 and 100.")
    
    def save(self, *args, **kwargs):
        """Override save to calculate available credit"""
        self.available_credit = self.credit_limit - self.current_balance
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if card is expired"""
        today = timezone.now().date()
        return (self.expiry_year < today.year or 
                (self.expiry_year == today.year and self.expiry_month < today.month))
    
    @property
    def is_expiring_soon(self, months=3):
        """Check if card expires within specified months"""
        today = timezone.now().date()
        future_date = today.replace(year=today.year + (today.month + months - 1) // 12,
                                   month=(today.month + months - 1) % 12 + 1)
        
        return (self.expiry_year < future_date.year or 
                (self.expiry_year == future_date.year and self.expiry_month <= future_date.month))
    
    @property
    def utilization_percentage(self):
        """Calculate credit utilization percentage"""
        if self.credit_limit == 0:
            return 0
        return (self.current_balance / self.credit_limit) * 100
    
    @property
    def days_until_due(self):
        """Calculate days until payment due date"""
        if not self.due_date:
            return None
        delta = self.due_date - timezone.now().date()
        return delta.days
    
    @property
    def is_payment_due_soon(self, days=7):
        """Check if payment is due within specified days"""
        if not self.due_date or self.days_until_due is None:
            return False
        return self.days_until_due <= days and self.days_until_due >= 0


class TransactionManager(models.Manager):
    """Custom manager for Transaction model"""
    
    def for_card(self, card):
        """Return transactions for a specific card"""
        return self.filter(credit_card=card)
    
    def for_month(self, year, month):
        """Return transactions for a specific month"""
        return self.filter(
            transaction_date__year=year,
            transaction_date__month=month
        )
    
    def by_category(self, category):
        """Return transactions by category"""
        return self.filter(category__icontains=category)
    
    def pending(self):
        """Return pending transactions"""
        return self.filter(is_pending=True)


class Transaction(BaseModel):
    """Transaction model for credit card transactions"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('payment', 'Payment'),
        ('fee', 'Fee'),
        ('interest', 'Interest'),
        ('credit', 'Credit/Refund'),
        ('cash_advance', 'Cash Advance'),
        ('balance_transfer', 'Balance Transfer'),
    ]
    
    credit_card = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        help_text="Credit card this transaction belongs to"
    )
    transaction_date = models.DateField(
        help_text="Date of transaction"
    )
    posted_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date transaction was posted to account"
    )
    description = models.CharField(
        max_length=200,
        help_text="Transaction description"
    )
    merchant = models.CharField(
        max_length=100,
        blank=True,
        help_text="Merchant name"
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Transaction category (e.g., Groceries, Gas, etc.)"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Transaction amount (positive for purchases, negative for payments/credits)"
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default='purchase',
        help_text="Type of transaction"
    )
    is_pending = models.BooleanField(
        default=False,
        help_text="Whether transaction is still pending"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about transaction"
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Transaction reference number"
    )
    
    objects = TransactionManager()
    
    class Meta:
        ordering = ['-transaction_date', '-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
    
    def __str__(self):
        return f"{self.merchant or self.description} - ${abs(self.amount)} ({self.transaction_date})"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.amount == 0:
            raise ValidationError("Transaction amount cannot be zero.")
        
        if self.transaction_date > timezone.now().date():
            raise ValidationError("Transaction date cannot be in the future.")
        
        if self.posted_date and self.posted_date < self.transaction_date:
            raise ValidationError("Posted date cannot be before transaction date.")


class PaymentManager(models.Manager):
    """Custom manager for Payment model"""
    
    def for_card(self, card):
        """Return payments for a specific card"""
        return self.filter(credit_card=card)
    
    def for_month(self, year, month):
        """Return payments for a specific month"""
        return self.filter(
            payment_date__year=year,
            payment_date__month=month
        )
    
    def scheduled(self):
        """Return scheduled payments"""
        return self.filter(is_scheduled=True, payment_date__gte=timezone.now().date())


class Payment(BaseModel):
    """Payment model for credit card payments"""
    
    PAYMENT_METHOD_CHOICES = [
        ('online', 'Online Banking'),
        ('autopay', 'Auto-pay'),
        ('check', 'Check'),
        ('phone', 'Phone Payment'),
        ('in_person', 'In Person'),
        ('other', 'Other'),
    ]
    
    credit_card = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        help_text="Credit card this payment is for"
    )
    payment_date = models.DateField(
        help_text="Date payment was/will be made"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Payment amount"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='online',
        help_text="Method used to make payment"
    )
    confirmation_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Payment confirmation number"
    )
    is_scheduled = models.BooleanField(
        default=False,
        help_text="Whether this is a scheduled future payment"
    )
    notes = models.TextField(
        blank=True,
        help_text="Payment notes"
    )
    
    objects = PaymentManager()
    
    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
    
    def __str__(self):
        return f"Payment of ${self.amount} for {self.credit_card.nickname} on {self.payment_date}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.amount <= 0:
            raise ValidationError("Payment amount must be greater than zero.")
        
        if not self.is_scheduled and self.payment_date > timezone.now().date():
            raise ValidationError("Payment date cannot be in the future unless it's scheduled.")
