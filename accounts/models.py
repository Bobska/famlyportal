from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import secrets
import string


class User(AbstractUser):
    """Custom User model extending AbstractUser"""
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', 
        blank=True, 
        null=True,
        help_text="Profile picture for the user"
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Phone number for the user"
    )
    date_of_birth = models.DateField(
        blank=True, 
        null=True,
        help_text="Date of birth"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_full_name() or 'No name'})"

    @property
    def age(self):
        """Calculate age from date of birth"""
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    @property
    def primary_family(self):
        """Get the user's primary family (first family they joined)"""
        family_member = self.familymember_set.order_by('joined_at').first()
        return family_member.family if family_member else None

    def is_family_admin(self, family=None):
        """Check if user is admin of specified family or any family"""
        if family:
            return self.familymember_set.filter(
                family=family, role='admin'
            ).exists()
        return self.familymember_set.filter(role='admin').exists()


class Family(models.Model):
    """Family model to group users"""
    name = models.CharField(
        max_length=100,
        help_text="Name of the family"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_families',
        help_text="User who created this family"
    )
    invite_code = models.CharField(
        max_length=8, 
        unique=True, 
        blank=True,
        help_text="Unique code for joining the family"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "families"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} Family"

    def save(self, *args, **kwargs):
        """Generate invite code if not provided"""
        if not self.invite_code:
            self.invite_code = self.generate_invite_code()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_invite_code():
        """Generate a unique 8-character invite code"""
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            if not Family.objects.filter(invite_code=code).exists():
                return code

    @property
    def member_count(self):
        """Get total number of family members"""
        return self.familymember_set.count()

    @property
    def admin_members(self):
        """Get all admin members"""
        return self.familymember_set.filter(role='admin')

    def get_member_by_user(self, user):
        """Get FamilyMember instance for a specific user"""
        try:
            return self.familymember_set.get(user=user)
        except FamilyMember.DoesNotExist:
            return None


class FamilyMember(models.Model):
    """Link between User and Family with role information"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('parent', 'Parent'),
        ('child', 'Child'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        help_text="User who is a member of the family"
    )
    family = models.ForeignKey(
        Family, 
        on_delete=models.CASCADE,
        help_text="Family the user belongs to"
    )
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='other',
        help_text="Role of the user in the family"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='invited_members',
        help_text="User who invited this member"
    )

    class Meta:
        unique_together = ['user', 'family']
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} - {self.family.name} ({self.get_role_display()})"

    @property
    def is_admin(self):
        """Check if this member is an admin"""
        return self.role == 'admin'

    @property
    def can_invite_members(self):
        """Check if this member can invite other members"""
        return self.role in ['admin', 'parent']

    @property
    def can_manage_family(self):
        """Check if this member can manage family settings"""
        return self.role == 'admin'
