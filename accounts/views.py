from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, ListView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db import transaction
from .models import User, Family, FamilyMember
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, 
    UserProfileForm, FamilyInviteForm, FamilyMemberRoleForm,
    AddFamilyMemberForm
)
from .decorators import (
    family_required, family_admin_required, get_user_family_context,
    FamilyPermissionMixin, can_user_manage_family_member
)


def user_register(request):
    """User registration view with family creation/joining"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    login(request, user)
                    
                    if form.cleaned_data['create_family']:
                        messages.success(
                            request, 
                            f"Welcome! You've successfully created the {form.cleaned_data['family_name']} family."
                        )
                    else:
                        family = Family.objects.get(invite_code=form.cleaned_data['invite_code'].upper())
                        messages.success(
                            request, 
                            f"Welcome! You've successfully joined the {family.name} family."
                        )
                    
                    return redirect('accounts:dashboard')
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            
            # Redirect to next parameter or dashboard
            next_url = request.GET.get('next', 'accounts:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def user_logout(request):
    """Logout view"""
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('accounts:login')


@login_required
def dashboard(request):
    """Main dashboard view"""
    context = get_user_family_context(request.user)
    
    # Add recent activity or summary data here in future
    context.update({
        'page_title': 'Dashboard',
        'show_family_invite': not context['family_count'],  # Show invite form if no families
    })
    
    return render(request, 'accounts/dashboard.html', context)


@login_required
def user_profile(request):
    """User profile management view"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=request.user)
    
    context = get_user_family_context(request.user)
    context.update({
        'form': form,
        'page_title': 'Profile',
    })
    
    return render(request, 'accounts/profile.html', context)


@login_required
def join_family(request):
    """Join an existing family using invite code"""
    if request.method == 'POST':
        form = FamilyInviteForm(request.POST)
        if form.is_valid():
            invite_code = form.cleaned_data['invite_code']
            
            try:
                family = Family.objects.get(invite_code=invite_code)
                
                # Check if user is already a member
                if FamilyMember.objects.filter(user=request.user, family=family).exists():
                    messages.warning(request, f"You are already a member of {family.name}.")
                else:
                    # Add user to family
                    FamilyMember.objects.create(
                        user=request.user,
                        family=family,
                        role='other'
                    )
                    messages.success(request, f"You have successfully joined {family.name}!")
                
                return redirect('accounts:dashboard')
            
            except Family.DoesNotExist:
                messages.error(request, "Invalid invite code.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FamilyInviteForm()
    
    context = get_user_family_context(request.user)
    context.update({
        'form': form,
        'page_title': 'Join Family',
    })
    
    return render(request, 'accounts/join_family.html', context)


@family_admin_required
def family_management(request):
    """Family management view for admins"""
    # Get families where user is admin
    admin_families = Family.objects.filter(
        familymember__user=request.user,
        familymember__role='admin'
    ).distinct()
    
    context = get_user_family_context(request.user)
    context.update({
        'admin_families': admin_families,
        'page_title': 'Family Management',
    })
    
    return render(request, 'accounts/family_management.html', context)


@family_admin_required
def family_members(request, family_pk):
    """View and manage family members"""
    family = get_object_or_404(Family, pk=family_pk)
    
    # Check if user is admin of this family
    if not request.user.is_family_admin(family):
        messages.error(request, "You don't have permission to manage this family.")
        return redirect('accounts:dashboard')
    
    members = family.familymember_set.select_related('user').order_by('joined_at')
    
    context = get_user_family_context(request.user)
    context.update({
        'family': family,
        'members': members,
        'page_title': f'{family.name} Members',
    })
    
    return render(request, 'accounts/family_members.html', context)


@family_admin_required
def update_member_role(request, family_pk, member_pk):
    """Update a family member's role"""
    family = get_object_or_404(Family, pk=family_pk)
    member = get_object_or_404(FamilyMember, pk=member_pk, family=family)
    
    # Check permissions
    if not can_user_manage_family_member(request.user, member):
        messages.error(request, "You don't have permission to modify this member.")
        return redirect('accounts:family_members', family_pk=family_pk)
    
    # Prevent removing last admin
    if member.role == 'admin' and family.admin_members.count() == 1:
        messages.error(request, "Cannot change role of the last admin. Promote another member first.")
        return redirect('accounts:family_members', family_pk=family_pk)
    
    if request.method == 'POST':
        form = FamilyMemberRoleForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(
                request, 
                f"Updated {member.user.get_full_name() or member.user.username}'s role to {member.get_role_display()}."
            )
            return redirect('accounts:family_members', family_pk=family_pk)
    else:
        form = FamilyMemberRoleForm(instance=member)
    
    context = get_user_family_context(request.user)
    context.update({
        'family': family,
        'member': member,
        'form': form,
        'page_title': f'Update {member.user.get_full_name() or member.user.username} Role',
    })
    
    return render(request, 'accounts/update_member_role.html', context)


@family_admin_required
def remove_family_member(request, family_pk, member_pk):
    """Remove a member from family"""
    family = get_object_or_404(Family, pk=family_pk)
    member = get_object_or_404(FamilyMember, pk=member_pk, family=family)
    
    # Check permissions
    if not can_user_manage_family_member(request.user, member):
        messages.error(request, "You don't have permission to remove this member.")
        return redirect('accounts:family_members', family_pk=family_pk)
    
    # Prevent removing last admin
    if member.role == 'admin' and family.admin_members.count() == 1:
        messages.error(request, "Cannot remove the last admin from the family.")
        return redirect('accounts:family_members', family_pk=family_pk)
    
    # Prevent self-removal if last admin
    if member.user == request.user and member.role == 'admin' and family.admin_members.count() == 1:
        messages.error(request, "You cannot remove yourself as the last admin. Transfer admin rights first.")
        return redirect('accounts:family_members', family_pk=family_pk)
    
    if request.method == 'POST':
        member_name = member.user.get_full_name() or member.user.username
        member.delete()
        messages.success(request, f"{member_name} has been removed from {family.name}.")
        
        # If user removed themselves, redirect to dashboard
        if member.user == request.user:
            return redirect('accounts:dashboard')
        
        return redirect('accounts:family_members', family_pk=family_pk)
    
    context = get_user_family_context(request.user)
    context.update({
        'family': family,
        'member': member,
        'page_title': f'Remove {member.user.get_full_name() or member.user.username}',
    })
    
    return render(request, 'accounts/remove_member_confirm.html', context)


@login_required
def family_invite_code(request, family_pk):
    """Get family invite code (AJAX)"""
    family = get_object_or_404(Family, pk=family_pk)
    
    # Check if user is member of this family
    if not FamilyMember.objects.filter(user=request.user, family=family).exists():
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    return JsonResponse({
        'invite_code': family.invite_code,
        'family_name': family.name
    })


@login_required
@family_admin_required
def add_family_member(request, family_pk):
    """Add a new family member (admin/parent only)"""
    family = get_object_or_404(Family, pk=family_pk)
    family_member = get_object_or_404(FamilyMember, user=request.user, family=family)
    
    # Check if user has permission to add members (admin or parent)
    if family_member.role not in ['admin', 'parent']:
        messages.error(request, "You don't have permission to add family members.")
        return redirect('accounts:family_members', family_pk=family.pk)
    
    if request.method == 'POST':
        form = AddFamilyMemberForm(request.POST, family=family)
        if form.is_valid():
            try:
                new_member = form.save()
                messages.success(
                    request, 
                    f"{new_member.user.get_full_name() or new_member.user.username} has been added to the family."
                )
                return redirect('accounts:family_members', family_pk=family.pk)
            except Exception as e:
                messages.error(request, f"Error adding family member: {str(e)}")
    else:
        form = AddFamilyMemberForm(family=family)
    
    context = get_user_family_context(request.user)
    context.update({
        'form': form,
        'family': family,
        'page_title': f'Add Member to {family.name}',
    })
    
    return render(request, 'accounts/add_family_member.html', context)
