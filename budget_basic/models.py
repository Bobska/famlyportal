from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()


class Payee(models.Model):
    """Payee/Merchant model for storing frequently used payee names"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Payee'
        verbose_name_plural = 'Payees'
        unique_together = ['user', 'name']  # Prevent duplicate payees per user
    
    def __str__(self):
        return self.name


class Income(models.Model):
    """Income transaction model for budget basic app"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    payee = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Income'
        verbose_name_plural = 'Income Entries'
    
    def __str__(self):
        return f"{self.payee} - ${self.amount} ({self.date})"


class Expense(models.Model):
    """Expense transaction model for budget basic app"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    payee = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Expense'
        verbose_name_plural = 'Expense Entries'
    
    def __str__(self):
        return f"{self.payee} - ${self.amount} ({self.date})"
