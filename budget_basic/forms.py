from django import forms
from .models import Income, Expense, Payee


class IncomeForm(forms.ModelForm):
    """Form for creating and editing income entries"""
    
    # Add payee selection field
    payee_choice = forms.ModelChoiceField(
        queryset=Payee.objects.none(),  # Will be set in __init__
        required=True,  # Make required since manual entry is removed
        empty_label="Select existing payee...",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_payee_choice'
        })
    )
    
    class Meta:
        model = Income
        fields = ['date', 'amount', 'notes']  # Remove payee from fields
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
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
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Set payee choices for the current user
            self.fields['payee_choice'].queryset = Payee.objects.filter(user=user).order_by('name')
    
    def clean(self):
        cleaned_data = super().clean()
        payee_choice = cleaned_data.get('payee_choice')
        
        # Payee choice is now required
        if not payee_choice:
            raise forms.ValidationError("Please select a payee.")
        
        # Set the payee name from the selected choice
        cleaned_data['payee'] = payee_choice.name
            
        return cleaned_data
    
    def clean_amount(self):
        """Clean and validate amount field"""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be positive.")
        return amount


class ExpenseForm(forms.ModelForm):
    """Form for creating and editing expense entries"""
    
    # Add payee selection field
    payee_choice = forms.ModelChoiceField(
        queryset=Payee.objects.none(),  # Will be set in __init__
        required=True,  # Make required since manual entry is removed
        empty_label="Select existing merchant...",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_payee_choice'
        })
    )
    
    class Meta:
        model = Expense
        fields = ['date', 'amount', 'notes']  # Remove payee from fields
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
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
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Set payee choices for the current user
            self.fields['payee_choice'].queryset = Payee.objects.filter(user=user).order_by('name')
    
    def clean(self):
        cleaned_data = super().clean()
        payee_choice = cleaned_data.get('payee_choice')
        
        # Payee choice is now required
        if not payee_choice:
            raise forms.ValidationError("Please select a merchant.")
        
        # Set the payee name from the selected choice
        cleaned_data['payee'] = payee_choice.name
            
        return cleaned_data
    
    def clean_amount(self):
        """Clean and validate amount field"""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be positive.")
        return amount