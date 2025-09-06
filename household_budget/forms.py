from django import forms
from .models import Category, Transaction


class TransactionForm(forms.ModelForm):
    """Form for creating and editing transactions"""
    
    def __init__(self, *args, **kwargs):
        family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if family:
            self.fields['category'].queryset = Category.objects.filter(family=family)
        else:
            self.fields['category'].queryset = Category.objects.none()
    
    class Meta:
        model = Transaction
        fields = ['merchant_payee', 'date', 'amount', 'transaction_type', 'category', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'merchant_payee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Grocery Store, Salary, etc.'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Optional notes...'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }


class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories"""
    
    def __init__(self, *args, **kwargs):
        family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if family:
            self.fields['parent'].queryset = Category.objects.filter(family=family)
        else:
            self.fields['parent'].queryset = Category.objects.none()
    
    class Meta:
        model = Category
        fields = ['name', 'parent', 'color']  # Exclude icon and sort_order to use model defaults
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
        }
