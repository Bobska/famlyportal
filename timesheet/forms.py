from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import TimeEntry, Project
from accounts.models import FamilyMember
from datetime import datetime, timedelta

User = get_user_model()


class TimeEntryForm(forms.ModelForm):
    """Form for creating and editing time entries"""
    
    class Meta:
        model = TimeEntry
        fields = ['project', 'date', 'start_time', 'end_time', 'break_duration', 'description', 'is_billable']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'break_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_billable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        # Custom widget for project field to include Bootstrap classes
        self.fields['project'].widget.attrs.update({'class': 'form-select'})
        
        # Filter projects by family
        if self.family:
            self.fields['project'].queryset = Project.objects.filter(
                family=self.family, 
                is_active=True
            ).order_by('name')
        else:
            self.fields['project'].queryset = Project.objects.none()
        
        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Validate date not in future
        if date and date > timezone.now().date():
            raise ValidationError("Date cannot be in the future.")
        
        # Validate time range
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError("End time must be after start time.")
        
        return cleaned_data


class ProjectForm(forms.ModelForm):
    """Form for creating and editing projects"""
    
    class Meta:
        model = Project
        fields = ['name', 'description', 'client_name', 'hourly_rate', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        self.created_by = kwargs.pop('created_by', None)
        super().__init__(*args, **kwargs)
    
    def clean_hourly_rate(self):
        hourly_rate = self.cleaned_data.get('hourly_rate')
        if hourly_rate is not None and hourly_rate < 0:
            raise ValidationError("Hourly rate cannot be negative.")
        return hourly_rate


class QuickEntryForm(forms.Form):
    """Simplified form for quick time logging"""
    project = forms.ModelChoiceField(
        queryset=Project.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a project"
    )
    hours_worked = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0.01'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional description...'})
    )
    date = forms.DateField(
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        # Filter projects by family
        if self.family:
            self.fields['project'].queryset = Project.objects.filter(
                family=self.family, 
                is_active=True
            ).order_by('name')
    
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise ValidationError("Date cannot be in the future.")
        return date


class ReportFilterForm(forms.Form):
    """Form for filtering timesheet reports"""
    date_range = forms.ChoiceField(
        choices=[
            ('week', 'This Week'),
            ('month', 'This Month'),
            ('quarter', 'This Quarter'),
            ('year', 'This Year'),
            ('custom', 'Custom Range'),
        ],
        initial='week',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="All projects"
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="All family members"
    )
    export_format = forms.ChoiceField(
        choices=[
            ('html', 'View in browser'),
            ('csv', 'Download CSV'),
            ('pdf', 'Download PDF'),
        ],
        initial='html',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if self.family:
            # Filter projects by family
            self.fields['project'].queryset = Project.objects.filter(family=self.family)
            
            # Filter users by family members
            family_member_ids = FamilyMember.objects.filter(family=self.family).values_list('user_id', flat=True)
            self.fields['user'].queryset = User.objects.filter(id__in=family_member_ids)
    
    def clean(self):
        cleaned_data = super().clean()
        date_range = cleaned_data.get('date_range')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if date_range == 'custom':
            if not start_date or not end_date:
                raise ValidationError("Start date and end date are required for custom range.")
            if start_date > end_date:
                raise ValidationError("Start date must be before end date.")
        
        return cleaned_data


class TimerForm(forms.Form):
    """Form for timer-based time tracking"""
    project = forms.ModelChoiceField(
        queryset=Project.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select a project"
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'What are you working on?'})
    )
    
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        if self.family:
            self.fields['project'].queryset = Project.objects.filter(
                family=self.family, 
                is_active=True
            ).order_by('name')
