"""
Subscription Tracker Forms

Comprehensive forms for subscription management with validation,
auto-completion, and family scoping.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms.widgets import DateInput
from decimal import Decimal
from .models import SubscriptionService, SubscriptionCategory, PaymentRecord

User = get_user_model()


class SubscriptionServiceForm(forms.ModelForm):
    """Main form for creating/editing subscription services"""
    
    # Common service suggestions for auto-complete
    COMMON_SERVICES = [
        'Netflix', 'Spotify', 'Amazon Prime', 'Disney+', 'Hulu', 'HBO Max',
        'Apple Music', 'YouTube Premium', 'Microsoft 365', 'Adobe Creative Cloud',
        'GitHub', 'Zoom Pro', 'Dropbox', 'Google Workspace', 'Slack',
        'Gym Membership', 'Insurance', 'Phone Plan', 'Internet', 'Utilities'
    ]
    
    used_by = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text='Select family members who use this subscription'
    )
    
    class Meta:
        model = SubscriptionService
        fields = [
            'name', 'category', 'cost', 'billing_cycle', 'start_date',
            'next_billing_date', 'website_url', 'description', 'status',
            'auto_renew', 'payment_method', 'used_by'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Netflix, Spotify, etc.',
                'list': 'common-services'
            }),
            'cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'billing_cycle': forms.Select(attrs={'class': 'form-select'}),
            'start_date': DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'next_billing_date': DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'website_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this subscription'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Visa ending in 1234'
            }),
            'category': forms.Select(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if family:
            # Filter categories and users by family
            self.fields['category'].queryset = SubscriptionCategory.objects.filter(family=family)
            self.fields['used_by'].queryset = User.objects.filter(
                familymember__family=family
            ).distinct()
    
    def clean_cost(self):
        cost = self.cleaned_data.get('cost')
        if cost and cost <= Decimal('0'):
            raise ValidationError('Cost must be greater than zero.')
        return cost
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        next_billing_date = cleaned_data.get('next_billing_date')
        
        if start_date and next_billing_date and next_billing_date < start_date:
            raise ValidationError('Next billing date cannot be before start date.')
        
        return cleaned_data


class SubscriptionCategoryForm(forms.ModelForm):
    """Form for creating/editing subscription categories"""
    
    class Meta:
        model = SubscriptionCategory
        fields = ['name', 'color', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Entertainment, Software, Health'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'style': 'height: 40px;'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional description for this category'
            })
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            return name.title()  # Capitalize properly
        return name


class QuickSubscriptionForm(forms.ModelForm):
    """Simplified form for dashboard quick-add"""
    
    class Meta:
        model = SubscriptionService
        fields = ['name', 'cost', 'billing_cycle']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Service name',
                'list': 'common-services'
            }),
            'cost': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
            'billing_cycle': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.family:
            instance.family = self.family
            # Set next billing date based on billing cycle
            from datetime import date, timedelta
            from dateutil.relativedelta import relativedelta
            
            today = date.today()
            if instance.billing_cycle == 'monthly':
                instance.next_billing_date = today + relativedelta(months=1)
            elif instance.billing_cycle == 'annually':
                instance.next_billing_date = today + relativedelta(years=1)
            elif instance.billing_cycle == 'quarterly':
                instance.next_billing_date = today + relativedelta(months=3)
            else:
                instance.next_billing_date = today + timedelta(days=30)
            
            instance.start_date = today
            
        if commit:
            instance.save()
        return instance


class SubscriptionFilterForm(forms.Form):
    """Form for filtering subscription list"""
    
    STATUS_CHOICES = [('', 'All Status')] + SubscriptionService.STATUS_CHOICES
    BILLING_CHOICES = [('', 'All Billing Cycles')] + SubscriptionService.BILLING_CYCLE_CHOICES
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search subscriptions...',
            'autocomplete': 'off'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=SubscriptionCategory.objects.none(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    billing_cycle = forms.ChoiceField(
        choices=BILLING_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    min_cost = forms.DecimalField(
        required=False,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Min cost'
        })
    )
    
    max_cost = forms.DecimalField(
        required=False,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Max cost'
        })
    )
    
    due_soon = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if family:
            self.fields['category'].queryset = SubscriptionCategory.objects.filter(family=family)


class BulkActionForm(forms.Form):
    """Form for bulk actions on subscriptions"""
    
    ACTION_CHOICES = [
        ('', 'Select Action'),
        ('pause', 'Pause Selected'),
        ('resume', 'Resume Selected'),
        ('cancel', 'Cancel Selected'),
        ('mark_paid', 'Mark as Paid'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        })
    )
    
    subscription_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_subscription_ids(self):
        ids_str = self.cleaned_data.get('subscription_ids', '')
        try:
            ids = [int(id_str.strip()) for id_str in ids_str.split(',') if id_str.strip()]
            return ids
        except ValueError:
            raise ValidationError('Invalid subscription IDs.')


class PaymentRecordForm(forms.ModelForm):
    """Form for recording manual payments"""
    
    class Meta:
        model = PaymentRecord
        fields = ['amount', 'payment_date', 'payment_method', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'payment_date': DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_method': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Visa ending in 1234'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this payment'
            })
        }


class SubscriptionSearchForm(forms.Form):
    """Advanced search form for subscriptions"""
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, description, or payment method...',
            'autocomplete': 'off'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
    
    def search(self):
        """Perform the search and return queryset"""
        if not self.family:
            return SubscriptionService.objects.none()
        
        query = self.cleaned_data.get('query', '').strip()
        qs = SubscriptionService.objects.filter(family=self.family)
        
        if query:
            from django.db.models import Q
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(payment_method__icontains=query) |
                Q(category__name__icontains=query)
            )
        
        return qs.distinct()
