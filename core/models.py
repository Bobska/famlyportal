from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class BaseModel(models.Model):
    """Abstract base model with common fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class FamilyScopedModel(BaseModel):
    """Abstract model for models that belong to a specific family"""
    family = models.ForeignKey(
        'accounts.Family',
        on_delete=models.CASCADE,
        help_text="Family this record belongs to"
    )

    class Meta:
        abstract = True

    def clean(self):
        """Ensure family-scoped validation"""
        super().clean()
        # Additional family-scoped validation can be added here


class UserScopedModel(BaseModel):
    """Abstract model for models that belong to a specific user"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User this record belongs to"
    )

    class Meta:
        abstract = True


class FamilyUserScopedModel(BaseModel):
    """Abstract model for models that belong to both a family and a user"""
    family = models.ForeignKey(
        'accounts.Family',
        on_delete=models.CASCADE,
        help_text="Family this record belongs to"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User this record belongs to"
    )

    class Meta:
        abstract = True

    def clean(self):
        """Ensure user belongs to the family"""
        super().clean()
        if (self.user_id and self.family_id and 
            not self.family.familymember_set.filter(user=self.user).exists()):
            raise ValidationError("User must be a member of the specified family.")


class StatusChoices(models.TextChoices):
    """Common status choices used across multiple models"""
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    PENDING = 'pending', 'Pending'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class PaymentStatusChoices(models.TextChoices):
    """Payment status choices"""
    PENDING = 'pending', 'Pending'
    PAID = 'paid', 'Paid'
    OVERDUE = 'overdue', 'Overdue'
    PARTIAL = 'partial', 'Partially Paid'
    CANCELLED = 'cancelled', 'Cancelled'


class PaymentMethodChoices(models.TextChoices):
    """Payment method choices"""
    CASH = 'cash', 'Cash'
    CHECK = 'check', 'Check'
    CREDIT_CARD = 'credit_card', 'Credit Card'
    DEBIT_CARD = 'debit_card', 'Debit Card'
    BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
    ONLINE = 'online', 'Online Payment'
    OTHER = 'other', 'Other'


class FrequencyChoices(models.TextChoices):
    """Frequency choices for recurring items"""
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    BIWEEKLY = 'biweekly', 'Bi-weekly'
    MONTHLY = 'monthly', 'Monthly'
    QUARTERLY = 'quarterly', 'Quarterly'
    YEARLY = 'yearly', 'Yearly'
