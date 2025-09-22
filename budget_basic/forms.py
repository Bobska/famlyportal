from django import forms
from .models import Income, Expense, Payee


class IncomeForm(forms.ModelForm):
    """Form for creating and editing income entries"""
    
    # Add payee selection field
    payee_choice = forms.ModelChoiceField(
        queryset=Payee.objects.none(),  # Will be set in __init__
        required=False,
        empty_label="Select existing payee...",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_payee_choice'
        })
    )
    
    # Keep original payee field for manual entry
    payee = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Or enter new payee name...',
            'id': 'id_payee_manual'
        })
    )
    
    class Meta:
        model = Income
        fields = ['date', 'payee', 'amount', 'notes']
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
        payee_manual = cleaned_data.get('payee')
        
        # Must have either a selected payee or manual entry
        if not payee_choice and not payee_manual:
            raise forms.ValidationError("Please select a payee or enter a new one.")
        
        # If both are provided, prioritize manual entry
        if payee_manual:
            cleaned_data['payee'] = payee_manual
        elif payee_choice:
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
        required=False,
        empty_label="Select existing payee...",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_payee_choice'
        })
    )
    
    # Keep original payee field for manual entry
    payee = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Or enter new payee name...',
            'id': 'id_payee_manual'
        })
    )
    
    class Meta:
        model = Expense
        fields = ['date', 'payee', 'amount', 'notes']
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
        payee_manual = cleaned_data.get('payee')
        
        # Must have either a selected payee or manual entry
        if not payee_choice and not payee_manual:
            raise forms.ValidationError("Please select a payee or enter a new one.")
        
        # If both are provided, prioritize manual entry
        if payee_manual:
            cleaned_data['payee'] = payee_manual
        elif payee_choice:
            cleaned_data['payee'] = payee_choice.name
            
        return cleaned_data
    
    def clean_amount(self):
        """Clean and validate amount field"""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be positive.")
        return amount