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


class UserPresence(models.Model):
    """
    Track real-time presence status for users.
    Used for online/offline indicators and last seen timestamps.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='presence',
        help_text="User whose presence is being tracked"
    )
    is_online = models.BooleanField(
        default=False,
        help_text="Whether the user is currently online"
    )
    last_seen = models.DateTimeField(
        auto_now=True,
        help_text="Last time the user was active"
    )
    last_heartbeat = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last heartbeat timestamp from WebSocket connection"
    )
    current_page = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Current page/module the user is viewing"
    )
    channel_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="WebSocket channel name for active connection"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "user presences"
        ordering = ['-last_seen']

    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        return f"{self.user.username} - {status}"

    def mark_online(self, channel_name=None, current_page=None):
        """Mark user as online"""
        self.is_online = True
        self.last_heartbeat = timezone.now()
        if channel_name:
            self.channel_name = channel_name
        if current_page:
            self.current_page = current_page
        self.save(update_fields=['is_online', 'last_heartbeat', 'channel_name', 'current_page', 'updated_at'])

    def mark_offline(self):
        """Mark user as offline"""
        self.is_online = False
        self.channel_name = None
        self.save(update_fields=['is_online', 'channel_name', 'updated_at'])

    def update_heartbeat(self, current_page=None):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = timezone.now()
        if current_page:
            self.current_page = current_page
        self.save(update_fields=['last_heartbeat', 'current_page', 'updated_at'])

    @property
    def time_since_last_seen(self):
        """Get human-readable time since last seen"""
        if self.is_online:
            return "Online now"
        
        delta = timezone.now() - self.last_seen
        if delta.seconds < 60:
            return "Just now"
        elif delta.seconds < 3600:
            minutes = delta.seconds // 60
            return f"{minutes}m ago"
        elif delta.seconds < 86400:
            hours = delta.seconds // 3600
            return f"{hours}h ago"
        else:
            days = delta.days
            return f"{days}d ago"

