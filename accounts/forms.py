from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, HTML
from crispy_forms.bootstrap import FormActions
from .models import User, Family, FamilyMember


class CustomUserCreationForm(UserCreationForm):
    """Custom user registration form"""
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    # Family options
    create_family = forms.BooleanField(
        required=False, 
        initial=True,
        label="Create a new family",
        help_text="Check this to create a new family, or uncheck to join an existing one."
    )
    family_name = forms.CharField(
        max_length=100, 
        required=False,
        label="Family name",
        help_text="Name for your new family (required if creating a family)"
    )
    invite_code = forms.CharField(
        max_length=8, 
        required=False,
        label="Family invite code",
        help_text="Enter the invite code to join an existing family"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'date_of_birth', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h3 class="mb-3">Account Information</h3>'),
            Row(
                Column('username', css_class='form-group col-md-6 mb-3'),
                Column('email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('phone_number', css_class='form-group col-md-6 mb-3'),
                Column('date_of_birth', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('password1', css_class='form-group col-md-6 mb-3'),
                Column('password2', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            HTML('<hr><h3 class="mb-3">Family Setup</h3>'),
            'create_family',
            'family_name',
            'invite_code',
            FormActions(
                Submit('submit', 'Create Account', css_class='btn btn-primary')
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        create_family = cleaned_data.get('create_family')
        family_name = cleaned_data.get('family_name')
        invite_code = cleaned_data.get('invite_code')

        if create_family and not family_name:
            raise ValidationError("Family name is required when creating a new family.")
        
        if not create_family and not invite_code:
            raise ValidationError("Invite code is required when joining an existing family.")
        
        if not create_family and invite_code:
            try:
                Family.objects.get(invite_code=invite_code.upper())
            except Family.DoesNotExist:
                raise ValidationError("Invalid invite code. Please check and try again.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.date_of_birth = self.cleaned_data['date_of_birth']
        
        if commit:
            user.save()
            
            # Handle family creation or joining
            create_family = self.cleaned_data['create_family']
            if create_family:
                # Create new family
                family = Family.objects.create(
                    name=self.cleaned_data['family_name'],
                    created_by=user
                )
                # Make user admin of the new family
                FamilyMember.objects.create(
                    user=user,
                    family=family,
                    role='admin'
                )
            else:
                # Join existing family
                invite_code = self.cleaned_data['invite_code'].upper()
                family = Family.objects.get(invite_code=invite_code)
                FamilyMember.objects.create(
                    user=user,
                    family=family,
                    role='other'  # Default role for new members
                )
        
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form with Bootstrap styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'password',
            FormActions(
                Submit('submit', 'Login', css_class='btn btn-primary w-100')
            )
        )
        # Add Bootstrap classes
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 
                 'date_of_birth', 'profile_picture']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'email',
            Row(
                Column('phone_number', css_class='form-group col-md-6 mb-3'),
                Column('date_of_birth', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'profile_picture',
            FormActions(
                Submit('submit', 'Update Profile', css_class='btn btn-primary')
            )
        )


class FamilyInviteForm(forms.Form):
    """Form for inviting users to join a family"""
    invite_code = forms.CharField(
        max_length=8,
        label="Family Invite Code",
        help_text="Enter the invite code to join a family"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'invite_code',
            FormActions(
                Submit('submit', 'Join Family', css_class='btn btn-primary')
            )
        )

    def clean_invite_code(self):
        invite_code = self.cleaned_data['invite_code'].upper()
        try:
            Family.objects.get(invite_code=invite_code)
        except Family.DoesNotExist:
            raise ValidationError("Invalid invite code. Please check and try again.")
        return invite_code


class CreateFamilyForm(forms.ModelForm):
    """Form for creating a new family"""
    
    class Meta:
        model = Family
        fields = ['name']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
            FormActions(
                Submit('submit', 'Create Family', css_class='btn btn-primary')
            )
        )
        
    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name.strip()) < 2:
            raise ValidationError("Family name must be at least 2 characters long.")
        return name.strip()


class FamilyMemberRoleForm(forms.ModelForm):
    """Form for updating family member roles (admin only)"""
    
    class Meta:
        model = FamilyMember
        fields = ['role']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'role',
            FormActions(
                Submit('submit', 'Update Role', css_class='btn btn-primary')
            )
        )


class AddFamilyMemberForm(forms.ModelForm):
    """Form for admins/parents to add new family members"""
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    username = forms.CharField(
        max_length=150, 
        required=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Your password must contain at least 8 characters."
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        help_text="Enter the same password as before, for verification."
    )
    
    class Meta:
        model = FamilyMember
        fields = ['role']
        
    def __init__(self, *args, **kwargs):
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)
        
        # Limit role choices based on who is creating the user
        self.fields['role'].choices = [
            ('child', 'Child'),
            ('other', 'Other'),
            ('parent', 'Parent'),
        ]
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-0'),
                Column('last_name', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'username',
            'email',
            Row(
                Column('password1', css_class='form-group col-md-6 mb-0'),
                Column('password2', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'role',
            FormActions(
                Submit('submit', 'Add Family Member', css_class='btn btn-success'),
                HTML('<a href="{% url "accounts:family_members" %}" class="btn btn-secondary">Cancel</a>')
            )
        )
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")
        return password2
    
    def save(self, commit=True):
        # Create the user first
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password1']
        )
        
        # Create the family member
        family_member = super().save(commit=False)
        family_member.user = user
        family_member.family = self.family
        
        if commit:
            family_member.save()
            
        return family_member
