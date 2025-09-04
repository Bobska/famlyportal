from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from accounts.models import Family, FamilyMember
from .models import Project, TimeEntry
from datetime import datetime, time

User = get_user_model()


class TimesheetModelsTest(TestCase):
    def setUp(self):
        # Create test user and family
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user
        )
        FamilyMember.objects.create(
            user=self.user,
            family=self.family,
            role='admin'
        )
        
        # Create test project
        self.project = Project.objects.create(
            name='Test Project',
            family=self.family,
            created_by=self.user,
            hourly_rate=50.00,
            description='A test project'
        )
    
    def test_project_creation(self):
        """Test that a project can be created"""
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.family, self.family)
        self.assertEqual(self.project.hourly_rate, 50.00)
        self.assertTrue(self.project.is_active)
    
    def test_time_entry_creation(self):
        """Test that a time entry can be created"""
        entry = TimeEntry.objects.create(
            user=self.user,
            project=self.project,
            date=timezone.now().date(),
            start_time=time(9, 0),
            end_time=time(17, 0),
            break_duration=60,  # 1 hour break
            description='Test work',
            is_billable=True
        )
        
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.project, self.project)
        self.assertEqual(entry.total_hours, 7.0)  # 8 hours - 1 hour break
        self.assertEqual(entry.earnings, 350.0)  # 7 hours * $50/hour
    
    def test_time_entry_calculations(self):
        """Test time and earnings calculations"""
        entry = TimeEntry.objects.create(
            user=self.user,
            project=self.project,
            date=timezone.now().date(),
            start_time=time(9, 0),
            end_time=time(12, 30),
            break_duration=30,  # 30 minute break
            is_billable=True
        )
        
        # 3.5 hours - 0.5 hour break = 3 hours
        self.assertEqual(entry.total_hours, 3.0)
        self.assertEqual(entry.earnings, 150.0)  # 3 hours * $50/hour
    
    def test_non_billable_entry(self):
        """Test non-billable entries don't generate earnings"""
        entry = TimeEntry.objects.create(
            user=self.user,
            project=self.project,
            date=timezone.now().date(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            is_billable=False
        )
        
        self.assertEqual(entry.total_hours, 3.0)
        self.assertEqual(entry.earnings, 0.0)  # Non-billable
    
    def test_project_without_rate(self):
        """Test projects without hourly rate"""
        project_no_rate = Project.objects.create(
            name='No Rate Project',
            family=self.family,
            created_by=self.user,
            hourly_rate=None
        )
        
        entry = TimeEntry.objects.create(
            user=self.user,
            project=project_no_rate,
            date=timezone.now().date(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            is_billable=True
        )
        
        self.assertEqual(entry.total_hours, 3.0)
        self.assertEqual(entry.earnings, 0.0)  # No rate set


class TimesheetViewsTest(TestCase):
    def setUp(self):
        # Create test user and family
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.family = Family.objects.create(
            name='Test Family',
            created_by=self.user
        )
        FamilyMember.objects.create(
            user=self.user,
            family=self.family,
            role='admin'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Create test project
        self.project = Project.objects.create(
            name='Test Project',
            family=self.family,
            created_by=self.user,
            hourly_rate=50.00
        )
    
    def test_dashboard_view(self):
        """Test that dashboard view loads correctly"""
        response = self.client.get(reverse('timesheet:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Timesheet Dashboard')
    
    def test_entries_list_view(self):
        """Test that entries list view loads correctly"""
        response = self.client.get(reverse('timesheet:entries'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Time Entries')
    
    def test_projects_list_view(self):
        """Test that projects list view loads correctly"""
        response = self.client.get(reverse('timesheet:projects'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Projects')
        self.assertContains(response, 'Test Project')
    
    def test_create_entry_view(self):
        """Test creating a new time entry"""
        response = self.client.get(reverse('timesheet:create_entry'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Time Entry')
    
    def test_create_project_view(self):
        """Test creating a new project"""
        response = self.client.get(reverse('timesheet:create_project'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Add Project')
    
    def test_reports_view(self):
        """Test that reports view loads correctly"""
        response = self.client.get(reverse('timesheet:reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Timesheet Reports')
