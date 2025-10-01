"""
Gmail Integration Views
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q

from .models import GmailAccount, EmailMessage, SyncLog
from .services import GmailService

logger = logging.getLogger(__name__)


@login_required
def account_list(request):
    """
    List Gmail accounts for current user
    """
    accounts = GmailAccount.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'accounts': accounts,
        'page_title': 'Gmail Accounts'
    }
    return render(request, 'gmail_integration/account_list.html', context)


@login_required
def add_account(request):
    """
    Initiate OAuth flow to add Gmail account
    """
    try:
        service = GmailService(user=request.user)
        
        # Build redirect URI
        redirect_uri = request.build_absolute_uri(reverse('gmail_integration:oauth_callback'))
        
        # Get authorization URL
        auth_url = service.get_authorization_url(redirect_uri)
        
        # Store redirect URI in session for callback
        request.session['gmail_redirect_uri'] = redirect_uri
        
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"Failed to initiate OAuth flow: {e}")
        messages.error(request, "Failed to connect to Gmail. Please try again.")
        return redirect('gmail_integration:account_list')


@login_required
def oauth_callback(request):
    """
    Handle OAuth callback from Google
    """
    logger.info("=" * 80)
    logger.info("OAuth Callback Started")
    logger.info(f"User: {request.user.username}")
    logger.info(f"GET params: {request.GET}")
    
    authorization_code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        logger.warning(f"OAuth error from Google: {error}")
        messages.error(request, f"Authorization failed: {error}")
        return redirect('gmail_integration:account_list')
    
    if not authorization_code:
        logger.warning("No authorization code in callback")
        messages.error(request, "No authorization code received.")
        return redirect('gmail_integration:account_list')
    
    logger.info(f"Authorization code received: {authorization_code[:20]}...")
    
    try:
        # Get redirect URI from session
        redirect_uri = request.session.get('gmail_redirect_uri')
        logger.info(f"Redirect URI from session: {redirect_uri}")
        
        if not redirect_uri:
            logger.error("No redirect URI found in session!")
            logger.error(f"Session keys: {list(request.session.keys())}")
            raise ValueError("No redirect URI found in session")
        
        logger.info("Creating GmailService...")
        # Handle OAuth callback
        service = GmailService(user=request.user)
        
        logger.info("Calling handle_oauth_callback...")
        gmail_account = service.handle_oauth_callback(authorization_code, redirect_uri)
        
        logger.info(f"Successfully created account: {gmail_account.email_address}")
        
        # Clean up session
        request.session.pop('gmail_redirect_uri', None)
        
        messages.success(
            request, 
            f"Successfully connected Gmail account: {gmail_account.email_address}"
        )
        
        # Redirect to account detail page
        return redirect('gmail_integration:account_detail', account_id=gmail_account.id)
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"OAuth callback failed with exception: {type(e).__name__}")
        logger.error(f"Exception message: {str(e)}")
        logger.error(f"Full traceback:", exc_info=True)
        logger.error("=" * 80)
        
        # Provide more detailed error message
        error_msg = str(e) if str(e) else "Unknown error occurred"
        messages.error(request, f"Failed to connect Gmail account: {error_msg}")
        return redirect('gmail_integration:account_list')



@login_required
def account_detail(request, account_id):
    """
    View Gmail account details and emails
    """
    account = get_object_or_404(GmailAccount, id=account_id, user=request.user)
    
    # Get recent emails
    emails = account.emails.all().order_by('-sent_date')[:20]
    
    # Get recent sync logs
    sync_logs = account.sync_logs.all().order_by('-started_at')[:10]
    
    context = {
        'account': account,
        'emails': emails,
        'sync_logs': sync_logs,
        'page_title': f'Gmail Account: {account.email_address}'
    }
    return render(request, 'gmail_integration/account_detail.html', context)


@login_required
def email_list(request, account_id):
    """
    List emails for a Gmail account with search and pagination
    """
    account = get_object_or_404(GmailAccount, id=account_id, user=request.user)
    
    # Get search query
    search = request.GET.get('search', '').strip()
    
    # Build queryset
    emails = account.emails.all()
    
    if search:
        emails = emails.filter(
            Q(subject__icontains=search) |
            Q(sender_email__icontains=search) |
            Q(sender_name__icontains=search) |
            Q(body_text__icontains=search)
        )
    
    # Order by date
    emails = emails.order_by('-sent_date')
    
    # Paginate
    paginator = Paginator(emails, 50)  # 50 emails per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'account': account,
        'page_obj': page_obj,
        'search': search,
        'page_title': f'Emails: {account.email_address}'
    }
    return render(request, 'gmail_integration/email_list.html', context)


@login_required
def email_detail(request, account_id, email_id):
    """
    View email details
    """
    account = get_object_or_404(GmailAccount, id=account_id, user=request.user)
    email = get_object_or_404(EmailMessage, id=email_id, gmail_account=account)
    
    context = {
        'account': account,
        'email': email,
        'page_title': f'Email: {email.subject[:50]}'
    }
    return render(request, 'gmail_integration/email_detail.html', context)


@login_required
@require_http_methods(["POST"])
def sync_emails(request, account_id):
    """
    Trigger email sync for account
    """
    account = get_object_or_404(GmailAccount, id=account_id, user=request.user)
    
    if not account.is_active:
        return JsonResponse({
            'success': False,
            'error': 'Account is not active'
        })
    
    try:
        # Get sync parameters
        query = request.POST.get('query', '')
        max_emails = int(request.POST.get('max_emails', 1000))
        
        # Start sync
        service = GmailService(gmail_account=account)
        sync_log = service.sync_emails(query=query, max_emails=max_emails)
        
        return JsonResponse({
            'success': True,
            'sync_log_id': sync_log.id,
            'message': f'Sync started for {account.email_address}'
        })
        
    except Exception as e:
        logger.error(f"Failed to start sync for account {account_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def sync_status(request, sync_log_id):
    """
    Get sync status
    """
    sync_log = get_object_or_404(SyncLog, id=sync_log_id, gmail_account__user=request.user)
    
    return JsonResponse({
        'status': sync_log.status,
        'message': sync_log.message or '',
        'emails_processed': sync_log.emails_processed,
        'emails_added': sync_log.emails_added,
        'emails_updated': sync_log.emails_updated,
        'errors_count': sync_log.errors_count,
        'started_at': sync_log.started_at.isoformat(),
        'completed_at': sync_log.completed_at.isoformat() if sync_log.completed_at else None
    })


@login_required
@require_http_methods(["POST"])
def toggle_account(request, account_id):
    """
    Toggle account active status
    """
    account = get_object_or_404(GmailAccount, id=account_id, user=request.user)
    
    account.is_active = not account.is_active
    account.save()
    
    status = "activated" if account.is_active else "deactivated"
    messages.success(request, f"Gmail account {status}")
    
    return redirect('gmail_integration:account_detail', account_id=account.id)


@login_required
@require_http_methods(["POST"])
def delete_account(request, account_id):
    """
    Delete Gmail account and all associated data
    """
    account = get_object_or_404(GmailAccount, id=account_id, user=request.user)
    
    email_address = account.email_address
    account.delete()
    
    messages.success(request, f"Gmail account {email_address} has been deleted")
    return redirect('gmail_integration:account_list')


@login_required
def sync_logs(request, account_id):
    """
    View sync logs for account
    """
    account = get_object_or_404(GmailAccount, id=account_id, user=request.user)
    
    # Get sync logs with pagination
    logs = account.sync_logs.all().order_by('-started_at')
    paginator = Paginator(logs, 20)  # 20 logs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'account': account,
        'logs': page_obj,  # Pass paginated logs as 'logs'
        'page_obj': page_obj,  # Also pass page_obj for pagination controls
        'page_title': f'Sync Logs: {account.email_address}'
    }
    return render(request, 'gmail_integration/sync_logs.html', context)


@login_required
def sync_log_detail(request, account_id, sync_log_id):
    """
    View detailed information about a specific sync log
    """
    account = get_object_or_404(GmailAccount, id=account_id, user=request.user)
    sync_log = get_object_or_404(SyncLog, id=sync_log_id, gmail_account=account)
    
    # Get emails from this sync if we can identify them by timestamp
    # (emails created/updated during this sync period)
    synced_emails = None
    if sync_log.completed_at:
        synced_emails = EmailMessage.objects.filter(
            gmail_account=account,
            received_date__gte=sync_log.started_at,
            received_date__lte=sync_log.completed_at
        ).order_by('-sent_date')[:50]  # Show first 50
    elif sync_log.started_at:
        # For incomplete syncs, show emails created after sync start
        synced_emails = EmailMessage.objects.filter(
            gmail_account=account,
            received_date__gte=sync_log.started_at
        ).order_by('-sent_date')[:50]
    
    # Calculate duration if completed
    duration = None
    if sync_log.started_at and sync_log.completed_at:
        duration = sync_log.completed_at - sync_log.started_at
    
    context = {
        'account': account,
        'sync_log': sync_log,
        'synced_emails': synced_emails,
        'duration': duration,
        'page_title': f'Sync Log Details: {sync_log.id}'
    }
    return render(request, 'gmail_integration/sync_log_detail.html', context)


# API-style views for AJAX integration

@login_required
def api_accounts(request):
    """
    API endpoint for user's Gmail accounts
    """
    accounts = GmailAccount.objects.filter(user=request.user, is_active=True)
    
    account_data = []
    for account in accounts:
        account_data.append({
            'id': account.id,
            'email_address': account.email_address,
            'display_name': account.display_name,
            'email_count': account.emails.count(),
            'last_sync_at': account.last_sync_at.isoformat() if account.last_sync_at else None,
            'sync_enabled': account.sync_enabled
        })
    
    return JsonResponse({'accounts': account_data})


@login_required
def api_search_emails(request, account_id):
    """
    API endpoint for searching emails
    """
    account = get_object_or_404(GmailAccount, id=account_id, user=request.user)
    
    search = request.GET.get('q', '').strip()
    limit = int(request.GET.get('limit', 20))
    
    if not search:
        return JsonResponse({'emails': []})
    
    # Search emails
    emails = account.emails.filter(
        Q(subject__icontains=search) |
        Q(sender_email__icontains=search) |
        Q(sender_name__icontains=search) |
        Q(body_text__icontains=search)
    ).order_by('-sent_date')[:limit]
    
    email_data = []
    for email in emails:
        email_data.append({
            'id': email.id,
            'gmail_id': email.gmail_id,
            'subject': email.subject,
            'sender_email': email.sender_email,
            'sender_name': email.sender_name,
            'sent_date': email.sent_date.isoformat(),
            'is_read': email.is_read,
            'has_attachments': email.has_attachments
        })
    
    return JsonResponse({'emails': email_data})
