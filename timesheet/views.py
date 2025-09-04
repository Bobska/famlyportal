from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from django.db import transaction
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date, parse_time
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime, timedelta, date
import csv
import json
from .models import TimeEntry, Project
from .forms import TimeEntryForm, ProjectForm, QuickEntryForm, ReportFilterForm, TimerForm
from accounts.decorators import family_required
from accounts.models import Family, FamilyMember

User = get_user_model()


def get_user_family(user):
    """Helper function to get user's family"""
    try:
        family_member = FamilyMember.objects.get(user=user)
        return family_member.family
    except FamilyMember.DoesNotExist:
        return None


@login_required
@family_required
def dashboard(request):
    """Main timesheet dashboard with overview and quick actions"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access the timesheet.")
        return redirect('accounts:join_family')
    
    # Get current week data
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # User's entries this week
    user_entries = TimeEntry.objects.filter(
        user=request.user,
        date__range=[week_start, week_end]
    ).select_related('project').order_by('-date', '-start_time')
    
    # Calculate weekly totals
    weekly_hours = sum(entry.total_hours for entry in user_entries)
    weekly_earnings = sum(entry.earnings for entry in user_entries)
    
    # Recent entries (last 5)
    recent_entries = TimeEntry.objects.filter(
        user=request.user
    ).select_related('project').order_by('-date', '-start_time')[:5]
    
    # Active projects
    active_projects = Project.objects.filter(
        family=family,
        is_active=True
    ).order_by('name')
    
    # Quick entry form
    quick_form = QuickEntryForm(family=family)
    
    # Timer form
    timer_form = TimerForm(family=family)
    
    # Statistics for the current month
    month_start = today.replace(day=1)
    month_entries = TimeEntry.objects.filter(
        user=request.user,
        date__gte=month_start
    )
    monthly_hours = sum(entry.total_hours for entry in month_entries)
    monthly_earnings = sum(entry.earnings for entry in month_entries)
    
    context = {
        'user_entries': user_entries,
        'recent_entries': recent_entries,
        'active_projects': active_projects,
        'quick_form': quick_form,
        'timer_form': timer_form,
        'weekly_hours': weekly_hours,
        'weekly_earnings': weekly_earnings,
        'monthly_hours': monthly_hours,
        'monthly_earnings': monthly_earnings,
        'week_start': week_start,
        'week_end': week_end,
        'today': today,
    }
    
    return render(request, 'timesheet/dashboard.html', context)


@login_required
@family_required
def time_entries(request):
    """List view for time entries with filtering and pagination"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access the timesheet.")
        return redirect('accounts:join_family')
    
    # Base queryset
    entries = TimeEntry.objects.filter(user=request.user).select_related('project')
    
    # Filtering
    project_id = request.GET.get('project')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if project_id:
        entries = entries.filter(project_id=project_id)
    
    if date_from:
        try:
            date_from = parse_date(date_from)
            entries = entries.filter(date__gte=date_from)
        except (ValueError, TypeError):
            pass
    
    if date_to:
        try:
            date_to = parse_date(date_to)
            entries = entries.filter(date__lte=date_to)
        except (ValueError, TypeError):
            pass
    
    # Ordering
    entries = entries.order_by('-date', '-start_time')
    
    # Pagination
    paginator = Paginator(entries, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Available projects for filter
    projects = Project.objects.filter(family=family).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'projects': projects,
        'current_project': project_id,
        'current_date_from': date_from,
        'current_date_to': date_to,
    }
    
    return render(request, 'timesheet/entries.html', context)


@login_required
@family_required
def create_entry(request):
    """Create a new time entry"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access the timesheet.")
        return redirect('accounts:join_family')
    
    if request.method == 'POST':
        form = TimeEntryForm(request.POST, user=request.user, family=family)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            messages.success(request, 'Time entry created successfully!')
            return redirect('timesheet:dashboard')
    else:
        form = TimeEntryForm(user=request.user, family=family)
    
    context = {
        'form': form,
        'title': 'Add Time Entry',
        'submit_text': 'Create Entry',
    }
    
    return render(request, 'timesheet/entry_form.html', context)


@login_required
@family_required
def edit_entry(request, entry_id):
    """Edit an existing time entry"""
    family = get_user_family(request.user)
    entry = get_object_or_404(TimeEntry, id=entry_id, user=request.user)
    
    if request.method == 'POST':
        form = TimeEntryForm(request.POST, instance=entry, user=request.user, family=family)
        if form.is_valid():
            form.save()
            messages.success(request, 'Time entry updated successfully!')
            return redirect('timesheet:entries')
    else:
        form = TimeEntryForm(instance=entry, user=request.user, family=family)
    
    context = {
        'form': form,
        'title': 'Edit Time Entry',
        'submit_text': 'Update Entry',
        'entry': entry,
    }
    
    return render(request, 'timesheet/entry_form.html', context)


@login_required
@family_required
def delete_entry(request, entry_id):
    """Delete a time entry"""
    entry = get_object_or_404(TimeEntry, id=entry_id, user=request.user)
    
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Time entry deleted successfully!')
        return redirect('timesheet:entries')
    
    context = {
        'entry': entry,
        'title': 'Delete Time Entry',
    }
    
    return render(request, 'timesheet/confirm_delete.html', context)


@login_required
@family_required
def projects(request):
    """List view for projects"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access the timesheet.")
        return redirect('accounts:join_family')
    
    projects_list = Project.objects.filter(family=family).order_by('name')
    
    # Add some statistics to each project
    for project in projects_list:
        entries = TimeEntry.objects.filter(project=project)
        project.stats = {
            'total_entries': entries.count(),
            'total_hours': sum(entry.total_hours for entry in entries),
            'total_earnings': sum(entry.earnings for entry in entries),
        }
    
    context = {
        'projects': projects_list,
    }
    
    return render(request, 'timesheet/projects.html', context)


@login_required
@family_required
def create_project(request):
    """Create a new project"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access the timesheet.")
        return redirect('accounts:join_family')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, family=family, created_by=request.user)
        if form.is_valid():
            project = form.save(commit=False)
            project.family = family
            project.created_by = request.user
            project.save()
            messages.success(request, 'Project created successfully!')
            return redirect('timesheet:projects')
    else:
        form = ProjectForm(family=family, created_by=request.user)
    
    context = {
        'form': form,
        'title': 'Add Project',
        'submit_text': 'Create Project',
    }
    
    return render(request, 'timesheet/project_form.html', context)


@login_required
@family_required
def edit_project(request, project_id):
    """Edit an existing project"""
    family = get_user_family(request.user)
    project = get_object_or_404(Project, id=project_id, family=family)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project, family=family, created_by=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('timesheet:projects')
    else:
        form = ProjectForm(instance=project, family=family, created_by=request.user)
    
    context = {
        'form': form,
        'title': 'Edit Project',
        'submit_text': 'Update Project',
        'project': project,
    }
    
    return render(request, 'timesheet/project_form.html', context)


@login_required
@family_required
def reports(request):
    """Reports and analytics view"""
    family = get_user_family(request.user)
    if not family:
        messages.error(request, "You must be part of a family to access the timesheet.")
        return redirect('accounts:join_family')
    
    form = ReportFilterForm(request.GET or None, family=family)
    
    # Default to current week
    today = timezone.now().date()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)
    selected_project = None
    selected_user = None
    
    if form.is_valid():
        date_range = form.cleaned_data.get('date_range')
        custom_start = form.cleaned_data.get('start_date')
        custom_end = form.cleaned_data.get('end_date')
        selected_project = form.cleaned_data.get('project')
        selected_user = form.cleaned_data.get('user')
        
        # Calculate date range
        if date_range == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif date_range == 'month':
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        elif date_range == 'quarter':
            quarter = (today.month - 1) // 3 + 1
            start_date = today.replace(month=(quarter - 1) * 3 + 1, day=1)
            end_month = quarter * 3
            if end_month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=end_month + 1, day=1) - timedelta(days=1)
        elif date_range == 'year':
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
        elif date_range == 'custom' and custom_start and custom_end:
            start_date = custom_start
            end_date = custom_end
    
    # Build queryset
    entries = TimeEntry.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('project', 'user')
    
    # Filter by project
    if selected_project:
        entries = entries.filter(project=selected_project)
    
    # Filter by user
    if selected_user:
        entries = entries.filter(user=selected_user)
    else:
        # Only show family members' entries
        family_user_ids = FamilyMember.objects.filter(family=family).values_list('user_id', flat=True)
        entries = entries.filter(user_id__in=family_user_ids)
    
    # Calculate totals
    total_hours = sum(entry.total_hours for entry in entries)
    total_earnings = sum(entry.earnings for entry in entries)
    total_entries = entries.count()
    
    # Calculate average hourly rate
    avg_hourly_rate = (total_earnings / total_hours) if total_hours > 0 else 0

    # Group by project
    project_data = {}
    for entry in entries:
        project_name = entry.project.name
        if project_name not in project_data:
            project_data[project_name] = {
                'hours': 0,
                'earnings': 0,
                'entries': 0,
            }
        project_data[project_name]['hours'] += entry.total_hours
        project_data[project_name]['earnings'] += entry.earnings
        project_data[project_name]['entries'] += 1
    
    # Add percentage calculations for projects
    for data in project_data.values():
        data['percentage'] = (data['hours'] / total_hours * 100) if total_hours > 0 else 0

    # Group by user
    user_data = {}
    for entry in entries:
        username = entry.user.get_full_name() or entry.user.username
        if username not in user_data:
            user_data[username] = {
                'hours': 0,
                'earnings': 0,
                'entries': 0,
            }
        user_data[username]['hours'] += entry.total_hours
        user_data[username]['earnings'] += entry.earnings
        user_data[username]['entries'] += 1

    # Add percentage calculations for users
    for data in user_data.values():
        data['percentage'] = (data['hours'] / total_hours * 100) if total_hours > 0 else 0

    context = {
        'form': form,
        'entries': entries.order_by('-date', '-start_time'),
        'total_hours': total_hours,
        'total_earnings': total_earnings,
        'total_entries': total_entries,
        'avg_hourly_rate': avg_hourly_rate,
        'project_data': project_data,
        'user_data': user_data,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'timesheet/reports.html', context)


# API Views for AJAX functionality

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def quick_entry_api(request):
    """API endpoint for quick time entry"""
    family = get_user_family(request.user)
    if not family:
        return JsonResponse({'error': 'No family found'}, status=400)
    
    try:
        data = json.loads(request.body)
        form = QuickEntryForm(data, family=family)
        
        if form.is_valid():
            # Convert hours to start/end time
            project = form.cleaned_data['project']
            hours = form.cleaned_data['hours_worked']
            description = form.cleaned_data['description']
            date = form.cleaned_data['date']
            
            # Create time entry
            entry = TimeEntry.objects.create(
                user=request.user,
                project=project,
                date=date,
                start_time=datetime.now().time(),
                end_time=(datetime.now() + timedelta(hours=float(hours))).time(),
                description=description,
                break_duration=0,
                is_billable=True,
            )
            
            return JsonResponse({
                'success': True,
                'entry_id': entry.pk,
                'message': 'Time entry created successfully!'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def start_timer_api(request):
    """API endpoint to start timer"""
    try:
        data = json.loads(request.body)
        project_id = data.get('project_id')
        description = data.get('description', '')
        
        family = get_user_family(request.user)
        project = get_object_or_404(Project, id=project_id, family=family)
        
        # Store timer info in session
        request.session['timer'] = {
            'project_id': project_id,
            'description': description,
            'start_time': timezone.now().isoformat(),
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Timer started!',
            'start_time': timezone.now().isoformat(),
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def stop_timer_api(request):
    """API endpoint to stop timer and create entry"""
    try:
        timer_data = request.session.get('timer')
        if not timer_data:
            return JsonResponse({
                'success': False,
                'error': 'No active timer found'
            }, status=400)
        
        start_time = timezone.datetime.fromisoformat(timer_data['start_time'])
        end_time = timezone.now()
        
        # Create time entry
        family = get_user_family(request.user)
        project = get_object_or_404(Project, id=timer_data['project_id'], family=family)
        
        entry = TimeEntry.objects.create(
            user=request.user,
            project=project,
            date=start_time.date(),
            start_time=start_time.time(),
            end_time=end_time.time(),
            description=timer_data['description'],
            break_duration=0,
            is_billable=True,
        )
        
        # Clear timer from session
        del request.session['timer']
        
        return JsonResponse({
            'success': True,
            'entry_id': entry.pk,
            'total_hours': entry.total_hours,
            'message': f'Timer stopped! Logged {entry.total_hours:.2f} hours.'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def get_timer_status_api(request):
    """API endpoint to get current timer status"""
    timer_data = request.session.get('timer')
    if timer_data:
        start_time = timezone.datetime.fromisoformat(timer_data['start_time'])
        elapsed = timezone.now() - start_time
        elapsed_seconds = elapsed.total_seconds()
        
        return JsonResponse({
            'active': True,
            'start_time': timer_data['start_time'],
            'elapsed_seconds': elapsed_seconds,
            'project_id': timer_data['project_id'],
            'description': timer_data['description'],
        })
    else:
        return JsonResponse({'active': False})


@login_required
@family_required
def export_csv(request):
    """Export time entries to CSV"""
    family = get_user_family(request.user)
    
    # Get filter parameters
    form = ReportFilterForm(request.GET, family=family)
    
    # Default date range
    today = timezone.now().date()
    start_date = today - timedelta(days=30)  # Last 30 days
    end_date = today
    
    if form.is_valid():
        # Apply same filtering logic as reports view
        # (Implementation similar to reports view)
        pass
    
    # Get entries
    entries = TimeEntry.objects.filter(
        date__range=[start_date, end_date],
        user=request.user
    ).select_related('project').order_by('-date', '-start_time')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="timesheet_{start_date}_to_{end_date}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Project', 'Start Time', 'End Time', 
        'Break (min)', 'Total Hours', 'Hourly Rate', 
        'Total Earnings', 'Description', 'Billable'
    ])
    
    for entry in entries:
        writer.writerow([
            entry.date,
            entry.project.name,
            entry.start_time,
            entry.end_time,
            entry.break_duration,
            entry.total_hours,
            entry.project.hourly_rate or 0,
            entry.earnings,
            entry.description,
            'Yes' if entry.is_billable else 'No',
        ])
    
    return response


# Legacy view aliases for compatibility
entry_list = time_entries
entry_create = create_entry
entry_detail = edit_entry
entry_update = edit_entry
entry_delete = delete_entry
job_list = projects
job_create = create_project
