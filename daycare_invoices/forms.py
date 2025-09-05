"""
Daycare Invoice Tracker Forms

Comprehensive forms for daycare provider, child, invoice and payment management
with family scoping and advanced validation.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import datetime

from .models import DaycareProvider, Child, Invoice, Payment
from core.models import PaymentStatusChoices, PaymentMethodChoices

User = get_user_model()


class DaycareProviderForm(forms.ModelForm):
    """Form for creating and editing daycare providers"""
    
    # Service options for providers
    SERVICES_CHOICES = [
        ('full_time', 'Full-time daycare'),
        ('part_time', 'Part-time daycare'),
        ('after_school', 'After-school care'),
        ('before_school', 'Before-school care'),
        ('summer_camp', 'Summer camp'),
        ('holiday_care', 'Holiday care'),
        ('infant_care', 'Infant care'),
        ('toddler_care', 'Toddler care'),
        ('preschool', 'Preschool program'),
        ('drop_in', 'Drop-in care'),
    ]
    
    services_offered = forms.MultipleChoiceField(
        choices=SERVICES_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text='Select all services this provider offers'
    )
    
    hourly_rate = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        help_text='Standard hourly rate if applicable'
    )
    
    daily_rate = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        help_text='Standard daily rate if applicable'
    )
    
    weekly_rate = forms.DecimalField(
        max_digits=7,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        help_text='Standard weekly rate if applicable'
    )
    
    monthly_rate = forms.DecimalField(
        max_digits=7,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        help_text='Standard monthly rate if applicable'
    )
    
    tax_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tax ID or business number'
        }),
        help_text='Tax ID or business registration number'
    )
    
    contract_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Contract start date'
    )
    
    contract_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text='Contract end date (if applicable)'
    )
    
    payment_terms_days = forms.IntegerField(
        initial=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '365'
        }),
        help_text='Number of days after invoice date that payment is due'
    )
    
    class Meta:
        model = DaycareProvider
        fields = [
            'name', 'contact_person', 'phone_number', 'email', 'address',
            'license_number', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Daycare provider name'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primary contact person'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@daycare.com'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Street address, city, state, zip code'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Daycare license number'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
    
    def clean_name(self):
        name = self.cleaned_data['name']
        
        # Check for duplicate provider names within the family
        if self.family:
            existing = DaycareProvider.objects.filter(
                family=self.family,
                name__iexact=name
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(f"A provider named '{name}' already exists for your family.")
        
        return name
    
    def clean(self):
        cleaned_data = super().clean()
        contract_start = cleaned_data.get('contract_start_date')
        contract_end = cleaned_data.get('contract_end_date')
        
        if contract_start and contract_end and contract_start >= contract_end:
            raise ValidationError('Contract end date must be after start date.')
        
        return cleaned_data


class ChildForm(forms.ModelForm):
    """Form for managing child enrollments"""
    
    # Schedule fields
    schedule_monday = forms.BooleanField(required=False, label='Monday')
    schedule_tuesday = forms.BooleanField(required=False, label='Tuesday')
    schedule_wednesday = forms.BooleanField(required=False, label='Wednesday')
    schedule_thursday = forms.BooleanField(required=False, label='Thursday')
    schedule_friday = forms.BooleanField(required=False, label='Friday')
    schedule_saturday = forms.BooleanField(required=False, label='Saturday')
    schedule_sunday = forms.BooleanField(required=False, label='Sunday')
    
    start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        help_text='Typical start time'
    )
    
    end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        help_text='Typical end time'
    )
    
    rate_override = forms.DecimalField(
        max_digits=7,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        help_text='Custom rate for this child (overrides provider default)'
    )
    
    medical_info = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Allergies, medical conditions, medications, etc.'
        }),
        help_text='Medical information and allergies'
    )
    
    class Meta:
        model = Child
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'provider',
            'start_date', 'is_enrolled', 'special_needs',
            'emergency_contact', 'emergency_phone'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'provider': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_enrolled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'special_needs': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Special needs, requirements, or notes'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency contact name'
            }),
            'emergency_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        # Filter providers by family
        if self.family:
            self.fields['provider'].queryset = DaycareProvider.objects.filter(
                family=self.family,
                is_active=True
            )
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        if dob > timezone.now().date():
            raise ValidationError('Date of birth cannot be in the future.')
        return dob
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise ValidationError('End time must be after start time.')
        
        return cleaned_data


class InvoiceForm(forms.ModelForm):
    """Form for creating and editing invoices"""
    
    # Additional service line items
    additional_services = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Additional services, fees, or charges'
        }),
        help_text='Line-by-line breakdown of additional services'
    )
    
    late_fee = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        help_text='Late fee amount if applicable'
    )
    
    discount_amount = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': '0.00'
        }),
        help_text='Discount amount if applicable'
    )
    
    tax_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=4,
        required=False,
        initial=Decimal('0.0000'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.0001',
            'placeholder': '0.0000'
        }),
        help_text='Tax rate (e.g., 0.0875 for 8.75%)'
    )
    
    auto_calculate_due_date = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Automatically calculate due date based on provider terms'
    )
    
    class Meta:
        model = Invoice
        fields = [
            'provider', 'child', 'invoice_number', 'invoice_date',
            'due_date', 'amount', 'status', 'description',
            'services_start_date', 'services_end_date'
        ]
        widgets = {
            'provider': forms.Select(attrs={
                'class': 'form-select'
            }),
            'child': forms.Select(attrs={
                'class': 'form-select'
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Provider invoice number'
            }),
            'invoice_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of services provided'
            }),
            'services_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'services_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        # Filter providers and children by family
        if self.family:
            self.fields['provider'].queryset = DaycareProvider.objects.filter(
                family=self.family,
                is_active=True
            )
            self.fields['child'].queryset = Child.objects.filter(
                family=self.family,
                is_enrolled=True
            )
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise ValidationError('Invoice amount must be positive.')
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        invoice_date = cleaned_data.get('invoice_date')
        due_date = cleaned_data.get('due_date')
        services_start = cleaned_data.get('services_start_date')
        services_end = cleaned_data.get('services_end_date')
        
        if invoice_date and due_date and due_date < invoice_date:
            raise ValidationError('Due date cannot be before invoice date.')
        
        if services_start and services_end and services_start > services_end:
            raise ValidationError('Service end date cannot be before start date.')
        
        return cleaned_data


class PaymentForm(forms.ModelForm):
    """Form for recording payments"""
    
    class Meta:
        model = Payment
        fields = [
            'invoice', 'payment_date', 'amount', 'method',
            'reference_number', 'notes'
        ]
        widgets = {
            'invoice': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Check number, transaction ID, etc.'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Payment notes'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        self.invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)
        
        # Filter invoices by family
        if self.family:
            self.fields['invoice'].queryset = Invoice.objects.filter(
                family=self.family
            ).exclude(status=PaymentStatusChoices.PAID)
        
        # Pre-select invoice if provided
        if self.invoice:
            self.fields['invoice'].initial = self.invoice
            # Set maximum amount to remaining balance
            remaining = self.invoice.remaining_balance
            self.fields['amount'].widget.attrs.update({
                'max': str(remaining),
                'placeholder': f'Max: ${remaining}'
            })
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        invoice = self.cleaned_data.get('invoice')
        
        if amount <= 0:
            raise ValidationError('Payment amount must be positive.')
        
        if invoice and amount > invoice.remaining_balance:
            raise ValidationError(
                f'Payment amount cannot exceed remaining balance of ${invoice.remaining_balance}'
            )
        
        return amount


class QuickInvoiceForm(forms.ModelForm):
    """Simplified form for quick invoice creation"""
    
    class Meta:
        model = Invoice
        fields = ['provider', 'child', 'amount', 'due_date', 'description']
        widgets = {
            'provider': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'child': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'date'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Service description'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if self.family:
            self.fields['provider'].queryset = DaycareProvider.objects.filter(
                family=self.family,
                is_active=True
            )
            self.fields['child'].queryset = Child.objects.filter(
                family=self.family,
                is_enrolled=True
            )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.family:
            instance.family = self.family
            instance.invoice_date = timezone.now().date()
        
        if commit:
            instance.save()
        return instance


class InvoiceFilterForm(forms.Form):
    """Form for filtering invoice list"""
    
    STATUS_CHOICES = [('', 'All Statuses')] + list(PaymentStatusChoices.choices)
    
    provider = forms.ModelChoiceField(
        queryset=DaycareProvider.objects.none(),
        required=False,
        empty_label='All Providers',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    child = forms.ModelChoiceField(
        queryset=Child.objects.none(),
        required=False,
        empty_label='All Children',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_range_start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'From date'
        })
    )
    
    date_range_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'To date'
        })
    )
    
    amount_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Min amount'
        })
    )
    
    amount_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Max amount'
        })
    )
    
    overdue_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if family:
            self.fields['provider'].queryset = DaycareProvider.objects.filter(family=family)
            self.fields['child'].queryset = Child.objects.filter(family=family)


class ProviderFilterForm(forms.Form):
    """Form for filtering provider list"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search providers...'
        })
    )
    
    active_only = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class PaymentFilterForm(forms.Form):
    """Form for filtering payment list"""
    
    METHOD_CHOICES = [('', 'All Methods')] + list(PaymentMethodChoices.choices)
    
    provider = forms.ModelChoiceField(
        queryset=DaycareProvider.objects.none(),
        required=False,
        empty_label='All Providers',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    child = forms.ModelChoiceField(
        queryset=Child.objects.none(),
        required=False,
        empty_label='All Children',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    method = forms.ChoiceField(
        choices=METHOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_range_start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_range_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def __init__(self, *args, **kwargs):
        family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if family:
            self.fields['provider'].queryset = DaycareProvider.objects.filter(family=family)
            self.fields['child'].queryset = Child.objects.filter(family=family)
