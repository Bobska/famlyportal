from django import forms
from .models import Income, Expense


class IncomeForm(forms.ModelForm):
    """Form for creating and editing income entries"""
    
    class Meta:
        model = Income
        fields = ['date', 'payee', 'amount', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'payee': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Employer, Client, Bank'
            }),
            'amount': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'pattern': r'[\d,]+\.?\d{0,2}'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Optional details...'
            })
        }
    
    def clean_amount(self):
        """Clean and validate amount field"""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be positive.")
        return amount


class ExpenseForm(forms.ModelForm):
    """Form for creating and editing expense entries"""
    
    class Meta:
        model = Expense
        fields = ['date', 'payee', 'amount', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'payee': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Store, Vendor, Service Provider'
            }),
            'amount': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'pattern': r'[\d,]+\.?\d{0,2}'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Optional details...'
            })
        }
    
    def clean_amount(self):
        """Clean and validate amount field"""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be positive.")
        return amount