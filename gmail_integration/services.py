"""
Gmail Service - Core business logic for Gmail integration
"""
import os
import json
import logging
import jwt
import socket
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from email.utils import parsedate_to_datetime

from django.conf import settings

# Force IPv4 for all socket connections (IPv6 times out on Windows)
# This fixes the WinError 10060 timeout issue
original_getaddrinfo = socket.getaddrinfo

def getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    """Force IPv4 resolution only"""
    return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

socket.getaddrinfo = getaddrinfo_ipv4_only
from django.utils import timezone as django_timezone
from django.contrib.auth.models import User

from google.auth.transport.requests import Request, AuthorizedSession
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpRequest
import google_auth_httplib2
import httplib2

from .models import GmailAccount, EmailMessage, EmailAttachment, SyncLog

logger = logging.getLogger(__name__)


class GmailService:
    """
    Service class for Gmail operations using Google API
    """
    
    # Gmail API scopes
    # Note: 'openid' is automatically added by Google when using userinfo scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid'  # Explicitly include to avoid scope mismatch errors
    ]
    
    def __init__(self, user: User = None, gmail_account: GmailAccount = None):
        """
        Initialize Gmail service
        
        Args:
            user: Django user (for creating new accounts)
            gmail_account: Existing Gmail account
        """
        self.user = user
        self.gmail_account = gmail_account
        self.service = None
        self._credentials = None
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        """
        Get OAuth2 authorization URL
        
        Args:
            redirect_uri: OAuth redirect URI
            
        Returns:
            Authorization URL
        """
        try:
            flow = Flow.from_client_secrets_file(
                settings.GOOGLE_OAUTH2_CLIENT_SECRETS_FILE,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Store state in session for verification
            return authorization_url
            
        except Exception as e:
            logger.error(f"Failed to get authorization URL: {e}")
            raise
    
    def handle_oauth_callback(self, authorization_code: str, redirect_uri: str) -> GmailAccount:
        """
        Handle OAuth2 callback and create/update Gmail account
        
        Args:
            authorization_code: Authorization code from Google
            redirect_uri: OAuth redirect URI
            
        Returns:
            GmailAccount instance
        """
        try:
            # Exchange authorization code for credentials
            flow = Flow.from_client_secrets_file(
                settings.GOOGLE_OAUTH2_CLIENT_SECRETS_FILE,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Get user info from Google
            user_info = self._get_user_info(credentials)
            email_address = user_info.get('email')
            display_name = user_info.get('name', '')
            
            if not email_address:
                raise ValueError("Could not retrieve email address from Google")
            
            # Create or update Gmail account
            gmail_account, created = GmailAccount.objects.get_or_create(
                email_address=email_address,
                defaults={
                    'user': self.user,
                    'display_name': display_name,
                    'is_active': True,
                    'sync_enabled': True
                }
            )
            
            if not created and gmail_account.user != self.user:
                raise ValueError(f"Gmail account {email_address} is already linked to another user")
            
            # Store encrypted credentials
            creds_dict = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            gmail_account.credentials = creds_dict
            gmail_account.display_name = display_name
            gmail_account.is_active = True
            gmail_account.save()
            
            self.gmail_account = gmail_account
            logger.info(f"Successfully {'created' if created else 'updated'} Gmail account: {email_address}")
            
            return gmail_account
            
        except Exception as e:
            logger.error(f"Failed to handle OAuth callback: {e}")
            raise
    
    def _get_user_info(self, credentials: Credentials) -> Dict:
        """
        Get user information from Google
        
        Tries to get user info from ID token first (faster, no network call),
        falls back to API call if needed.
        """
        try:
            # Try to get info from ID token first (OpenID Connect)
            if hasattr(credentials, 'id_token') and credentials.id_token:
                # Decode without verification since we just got it from Google
                user_info = jwt.decode(credentials.id_token, options={"verify_signature": False})
                logger.info(f"Got user info from ID token: {user_info.get('email')}")
                return {
                    'email': user_info.get('email'),
                    'name': user_info.get('name', ''),
                    'picture': user_info.get('picture', '')
                }
            
            # Fallback: Make API call to get user info
            logger.info("ID token not available, making API call for user info...")
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            return user_info
            
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            raise
    
    def authenticate(self) -> bool:
        """
        Authenticate and build Gmail service
        
        Returns:
            True if authentication successful
        """
        if not self.gmail_account:
            raise ValueError("No Gmail account provided")
        
        try:
            creds_dict = self.gmail_account.credentials
            if not creds_dict:
                raise ValueError("No credentials found for Gmail account")
            
            # Create credentials object
            credentials = Credentials(
                token=creds_dict.get('token'),
                refresh_token=creds_dict.get('refresh_token'),
                token_uri=creds_dict.get('token_uri'),
                client_id=creds_dict.get('client_id'),
                client_secret=creds_dict.get('client_secret'),
                scopes=creds_dict.get('scopes')
            )
            
            # Refresh token if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                
                # Update stored credentials
                updated_creds = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes
                }
                self.gmail_account.credentials = updated_creds
                self.gmail_account.save()
            
            # CRITICAL FIX: Use requests library directly instead of httplib2
            # The Google API Python client defaults to httplib2 which has
            # connectivity issues on Windows. The requests library works fine.
            # We'll use a monkey-patch approach to force requests usage.
            
            # Save the original build function behavior but use requests
            import os
            os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
            
            # Use the default build which will use httplib2
            # But we set a longer timeout via socket
            import socket
            socket.setdefaulttimeout(60)
            
            # Try to force requests usage by checking for google-auth-httplib2
            try:
                # Build service - will use httplib2 by default
                self.service = build('gmail', 'v1', credentials=credentials, cache_discovery=False)
                self._credentials = credentials
                
                # Monkey-patch the service's http instance to use longer timeouts
                if hasattr(self.service, '_http'):
                    if hasattr(self.service._http, 'timeout'):
                        self.service._http.timeout = 60
                    # Try to set timeout on the underlying http object
                    if hasattr(self.service._http, 'http'):
                        if hasattr(self.service._http.http, 'timeout'):
                            self.service._http.http.timeout = 60
                        
            except Exception as e:
                logger.error(f"Failed to build service with extended timeout: {e}")
                # Fallback to standard build
                self.service = build('gmail', 'v1', credentials=credentials)
                self._credentials = credentials
            
            logger.info(f"Successfully authenticated Gmail account: {self.gmail_account.email_address}")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed for {self.gmail_account.email_address}: {e}")
            return False
    
    def get_emails(self, query: str = "", max_results: int = 100, page_token: str = None) -> Tuple[List[Dict], str]:
        """
        Get emails from Gmail using requests library directly (bypassing httplib2 issues)
        
        Args:
            query: Gmail search query
            max_results: Maximum number of emails to return
            page_token: Page token for pagination
            
        Returns:
            Tuple of (email list, next_page_token)
        """
        if not self._credentials:
            if not self.authenticate():
                raise ValueError("Failed to authenticate Gmail service")
        
        try:
            # Always refresh token before API calls to ensure it's valid
            # Note: Google's expired check isn't reliable - token may be expired
            # even when credentials.expired is False
            if self._credentials.refresh_token:
                logger.info("Refreshing token to ensure it's valid...")
                self._credentials.refresh(Request())
                
                # Update stored credentials
                updated_creds = {
                    'token': self._credentials.token,
                    'refresh_token': self._credentials.refresh_token,
                    'token_uri': self._credentials.token_uri,
                    'client_id': self._credentials.client_id,
                    'client_secret': self._credentials.client_secret,
                    'scopes': self._credentials.scopes
                }
                self.gmail_account.credentials = updated_creds
                self.gmail_account.save()
                logger.info("Token refreshed successfully")
            
            # BYPASS HTTPLIB2: Use requests library directly
            # This avoids the WinError 10060 timeout issue with httplib2
            import requests
            
            # Build URL with parameters
            url = 'https://gmail.googleapis.com/gmail/v1/users/me/messages'
            params = {
                'maxResults': max_results
            }
            if query:
                params['q'] = query
            if page_token:
                params['pageToken'] = page_token
            
            # Make request with auth header
            headers = {
                'Authorization': f'Bearer {self._credentials.token}',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            results = response.json()
            messages = results.get('messages', [])
            next_page_token = results.get('nextPageToken')
            
            # Get full message details
            email_list = []
            for message in messages:
                try:
                    email_data = self.get_email_by_id(message['id'])
                    if email_data:
                        email_list.append(email_data)
                except Exception as e:
                    logger.warning(f"Failed to get email {message['id']}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(email_list)} emails from Gmail using requests library")
            return email_list, next_page_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Gmail API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get emails: {e}")
            raise
    
    def get_email_by_id(self, email_id: str) -> Optional[Dict]:
        """
        Get email details by Gmail ID using requests library directly
        
        Args:
            email_id: Gmail message ID
            
        Returns:
            Email data dictionary or None
        """
        if not self._credentials:
            if not self.authenticate():
                raise ValueError("Failed to authenticate Gmail service")
        
        try:
            # BYPASS HTTPLIB2: Use requests library directly
            import requests
            
            url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{email_id}'
            params = {'format': 'full'}
            headers = {
                'Authorization': f'Bearer {self._credentials.token}',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            message = response.json()
            return self._parse_email_message(message)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Gmail API error getting email {email_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get email {email_id}: {e}")
            return None
    
    def _parse_email_message(self, message: Dict) -> Dict:
        """
        Parse Gmail message into structured data with timezone-aware datetimes
        
        Args:
            message: Raw Gmail message
            
        Returns:
            Parsed email data
        """
        try:
            headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
            
            # Extract basic metadata
            email_data = {
                'gmail_id': message['id'],
                'thread_id': message['threadId'],
                'subject': headers.get('Subject', ''),
                'sender_email': self._extract_email(headers.get('From', '')),
                'sender_name': self._extract_name(headers.get('From', '')),
                'recipient_emails': self._parse_email_list(headers.get('To', '')),
                'cc_emails': self._parse_email_list(headers.get('Cc', '')),
                'bcc_emails': self._parse_email_list(headers.get('Bcc', '')),
                'labels': message.get('labelIds', []),
                'is_read': 'UNREAD' not in message.get('labelIds', []),
                'is_important': 'IMPORTANT' in message.get('labelIds', []),
            }
            
            # Parse date (ensure timezone-aware to avoid RuntimeWarning)
            date_str = headers.get('Date', '')
            if date_str:
                try:
                    parsed_date = parsedate_to_datetime(date_str)
                    # Ensure timezone-aware - parsedate_to_datetime should return aware datetime
                    # but if not, make it UTC
                    if parsed_date.tzinfo is None:
                        from datetime import timezone as dt_timezone
                        parsed_date = parsed_date.replace(tzinfo=dt_timezone.utc)
                    email_data['sent_date'] = parsed_date
                except:
                    email_data['sent_date'] = django_timezone.now()
            else:
                email_data['sent_date'] = django_timezone.now()
            
            # Extract body content and attachments
            body_text, body_html, attachments = self._extract_content_and_attachments(message['payload'])
            email_data['body_text'] = body_text
            email_data['body_html'] = body_html
            email_data['has_attachments'] = len(attachments) > 0
            email_data['attachment_count'] = len(attachments)
            email_data['attachments'] = attachments
            
            return email_data
            
        except Exception as e:
            logger.error(f"Failed to parse email message: {e}")
            raise
    
    def _extract_content_and_attachments(self, payload: Dict) -> Tuple[str, str, List[Dict]]:
        """Extract email body content and attachment metadata"""
        body_text = ""
        body_html = ""
        attachments = []
        
        def process_part(part):
            nonlocal body_text, body_html, attachments
            
            if part.get('filename'):
                # This is an attachment
                attachment_data = {
                    'filename': part['filename'],
                    'content_type': part['mimeType'],
                    'size_bytes': part.get('body', {}).get('size', 0),
                    'attachment_id': part.get('body', {}).get('attachmentId', '')
                }
                attachments.append(attachment_data)
                return
            
            mime_type = part.get('mimeType', '')
            
            if mime_type == 'text/plain':
                data = part.get('body', {}).get('data')
                if data:
                    import base64
                    decoded = base64.urlsafe_b64decode(data + '===').decode('utf-8')
                    body_text += decoded
            elif mime_type == 'text/html':
                data = part.get('body', {}).get('data')
                if data:
                    import base64
                    decoded = base64.urlsafe_b64decode(data + '===').decode('utf-8')
                    body_html += decoded
            elif mime_type.startswith('multipart/'):
                # Process nested parts
                for subpart in part.get('parts', []):
                    process_part(subpart)
        
        if 'parts' in payload:
            for part in payload['parts']:
                process_part(part)
        else:
            process_part(payload)
        
        return body_text.strip(), body_html.strip(), attachments
    
    def _extract_email(self, from_header: str) -> str:
        """Extract email address from From header"""
        import re
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_header)
        return match.group(0) if match else from_header
    
    def _extract_name(self, from_header: str) -> str:
        """Extract name from From header"""
        import re
        # Check for "Name <email>" format
        match = re.match(r'^([^<]+)<', from_header)
        if match:
            return match.group(1).strip().strip('"')
        return ""
    
    def _parse_email_list(self, email_string: str) -> List[str]:
        """Parse comma-separated email list"""
        if not email_string:
            return []
        
        import re
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', email_string)
        return emails
    
    def _should_cancel_sync(self, sync_log_id: int) -> bool:
        """
        Check if sync should be cancelled by checking database status
        Returns True if sync_log status is 'cancelled'
        """
        try:
            from .models import SyncLog
            sync_log = SyncLog.objects.get(id=sync_log_id)
            return sync_log.status == 'cancelled'
        except Exception:
            return False
    
    def get_all_message_ids(self, query: str = "", max_messages: int = 5000) -> List[str]:
        """
        Get list of ALL message IDs from Gmail (lightweight, no full message data)
        Much faster than fetching full messages
        
        Args:
            query: Gmail search query
            max_messages: Maximum number of message IDs to retrieve
            
        Returns:
            List of Gmail message IDs
        """
        if not self._credentials:
            if not self.authenticate():
                raise ValueError("Failed to authenticate Gmail service")
        
        try:
            import requests
            
            all_message_ids = []
            page_token = None
            
            while len(all_message_ids) < max_messages:
                url = 'https://gmail.googleapis.com/gmail/v1/users/me/messages'
                params = {
                    'maxResults': min(500, max_messages - len(all_message_ids)),  # Max 500 per request
                    'fields': 'messages/id,nextPageToken'  # Only get IDs, not full data
                }
                if query:
                    params['q'] = query
                if page_token:
                    params['pageToken'] = page_token
                
                headers = {
                    'Authorization': f'Bearer {self._credentials.token}',
                    'Accept': 'application/json'
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                
                results = response.json()
                messages = results.get('messages', [])
                
                if not messages:
                    break
                
                all_message_ids.extend([msg['id'] for msg in messages])
                page_token = results.get('nextPageToken')
                
                if not page_token:
                    break
            
            logger.info(f"Retrieved {len(all_message_ids)} message IDs from Gmail")
            return all_message_ids
            
        except Exception as e:
            logger.error(f"Failed to get message IDs: {e}")
            raise
    
    def get_new_message_ids(self, query: str = "", max_messages: int = 5000) -> Tuple[List[str], int, int]:
        """
        Get list of message IDs that don't exist in database yet
        
        Args:
            query: Gmail search query
            max_messages: Maximum number of messages to check
            
        Returns:
            Tuple of (new_message_ids, total_in_gmail, already_synced_count)
        """
        # Get all message IDs from Gmail
        all_gmail_ids = self.get_all_message_ids(query, max_messages)
        total_count = len(all_gmail_ids)
        
        if not all_gmail_ids:
            return [], 0, 0
        
        # Check which ones already exist in database
        existing_ids = set(
            self.gmail_account.emails.filter(
                gmail_id__in=all_gmail_ids
            ).values_list('gmail_id', flat=True)
        )
        
        # Find new IDs (not in database)
        new_ids = [gid for gid in all_gmail_ids if gid not in existing_ids]
        
        already_synced = len(existing_ids)
        
        logger.info(f"Gmail: {total_count} total, {already_synced} already synced, {len(new_ids)} new")
        return new_ids, total_count, already_synced
    
    def fetch_emails_by_ids(self, message_ids: List[str]) -> List[Dict]:
        """
        Fetch full email data for specific message IDs
        
        Args:
            message_ids: List of Gmail message IDs to fetch
            
        Returns:
            List of email data dictionaries
        """
        emails = []
        for msg_id in message_ids:
            try:
                email_data = self.get_email_by_id(msg_id)
                if email_data:
                    emails.append(email_data)
            except Exception as e:
                logger.warning(f"Failed to fetch email {msg_id}: {e}")
                continue
        
        return emails
    
    def sync_emails_incremental(self, query: str = "", max_emails: int = 5000) -> SyncLog:
        """
        OPTIMIZED: Incremental sync that only processes NEW emails
        Phase 1: Quick scan to find what's new
        Phase 2: Process only new emails
        
        Much faster than sync_emails() because it skips already-synced emails
        
        Args:
            query: Gmail search query
            max_emails: Maximum number of emails to check
            
        Returns:
            SyncLog instance
        """
        if not self.gmail_account:
            raise ValueError("No Gmail account provided")
        
        # Create sync log
        sync_log = SyncLog.objects.create(
            gmail_account=self.gmail_account,
            status='started',
            message='🔍 Scanning for new emails...'
        )
        
        try:
            # PHASE 1: Quick Discovery (Fast!)
            from .models import SyncHistoryEvent
            
            # History Event: Starting scan
            SyncHistoryEvent.objects.create(
                sync_log=sync_log,
                event_type='start',
                message='🔍 Phase 1: Scanning Gmail for new emails (this is fast)...',
                emails_processed=0
            )
            
            sync_log.message = '🔍 Phase 1: Scanning Gmail for new emails (this is fast)...'
            sync_log.save(update_fields=['message'])
            
            # Get list of new message IDs only
            new_message_ids, total_in_gmail, already_synced = self.get_new_message_ids(query, max_emails)
            
            # History Event: Scan results
            SyncHistoryEvent.objects.create(
                sync_log=sync_log,
                event_type='progress',
                message=f'📊 Found {total_in_gmail} emails: {already_synced} already synced, {len(new_message_ids)} new to process',
                emails_processed=0
            )
            
            # Update with discovery results
            sync_log.message = f'📊 Found {total_in_gmail} emails: {already_synced} already synced, {len(new_message_ids)} new to process'
            sync_log.save(update_fields=['message'])
            
            if len(new_message_ids) == 0:
                sync_log.status = 'success'
                sync_log.completed_at = timezone.now()
                sync_log.message = f'✅ Already up to date! All {total_in_gmail} emails are synced'
                sync_log.save()
                
                # History Event: Already up to date
                SyncHistoryEvent.objects.create(
                    sync_log=sync_log,
                    event_type='finish',
                    message=f'✅ Already up to date! All {total_in_gmail} emails are synced',
                    emails_processed=0
                )
                
                return sync_log
            
            # PHASE 2: Process ONLY new emails (Much faster!)
            # History Event: Starting Phase 2
            SyncHistoryEvent.objects.create(
                sync_log=sync_log,
                event_type='process',
                message=f'⚙️ Phase 2: Processing {len(new_message_ids)} new emails...',
                emails_processed=0
            )
            
            sync_log.message = f'⚙️ Phase 2: Processing {len(new_message_ids)} new emails...'
            sync_log.save(update_fields=['message'])
            
            emails_processed = 0
            emails_added = 0
            emails_updated = 0
            errors_count = 0
            cancelled = False
            
            # Process new emails in batches of 10
            batch_size = 10
            total_new = len(new_message_ids)
            
            for i in range(0, len(new_message_ids), batch_size):
                # Check for cancellation
                if self._should_cancel_sync(sync_log.id):
                    logger.info(f"Sync {sync_log.id} cancelled by user, stopping...")
                    cancelled = True
                    
                    # Final message for cancellation
                    sync_log.message = f'🛑 Sync cancelled. Processed {emails_processed}/{total_new} new emails'
                    sync_log.save(update_fields=['message'])
                    
                    # History Event: Cancellation
                    SyncHistoryEvent.objects.create(
                        sync_log=sync_log,
                        event_type='cancel',
                        message=f'🛑 Sync cancelled. Processed {emails_processed}/{total_new} new emails',
                        emails_processed=emails_processed,
                        emails_added=emails_added,
                        emails_updated=emails_updated
                    )
                    break
                
                batch_ids = new_message_ids[i:i+batch_size]
                
                # Fetch emails (silent, no history event)
                email_list = self.fetch_emails_by_ids(batch_ids)
                
                # Process each email
                for email_data in email_list:
                    # Check cancellation every 10 emails
                    if emails_processed % 10 == 0 and self._should_cancel_sync(sync_log.id):
                        cancelled = True
                        break
                    
                    try:
                        email_obj, created = self._save_email_to_db(email_data)
                        if created:
                            emails_added += 1
                        else:
                            emails_updated += 1
                        emails_processed += 1
                        
                        # Calculate percentage
                        percentage = int((emails_processed / total_new) * 100)
                        
                        # Update MAIN message (this shows in live tracker - updates continuously)
                        sync_log.emails_processed = emails_processed
                        sync_log.emails_added = emails_added
                        sync_log.emails_updated = emails_updated
                        sync_log.message = f'⚙️ Processing: {emails_processed}/{total_new} new emails ({percentage}%)'
                        sync_log.save(update_fields=['emails_processed', 'emails_added', 'emails_updated', 'message'])
                        
                    except Exception as e:
                        errors_count += 1
                        logger.error(f"Failed to save email {email_data.get('gmail_id')}: {e}")
                
                if cancelled:
                    break
            
            # Final update
            sync_log.emails_processed = emails_processed
            sync_log.emails_added = emails_added
            sync_log.emails_updated = emails_updated
            sync_log.errors_count = errors_count
            
            if cancelled:
                sync_log.status = 'cancelled'
                sync_log.message = f'🛑 Sync cancelled. Processed {emails_processed}/{total_new} new emails'
            elif errors_count > 0:
                sync_log.status = 'partial'
                sync_log.message = f'⚠️ Partial success: {emails_processed} new emails, {errors_count} errors'
                
                # History Event: Partial completion
                SyncHistoryEvent.objects.create(
                    sync_log=sync_log,
                    event_type='finish',
                    message=f'⚠️ Partial success: {emails_processed} new emails, {errors_count} errors',
                    emails_processed=emails_processed,
                    emails_added=emails_added,
                    emails_updated=emails_updated
                )
            else:
                # Update final progress message to "Processed" (past tense)
                sync_log.message = f'⚙️ Processed: {emails_processed}/{total_new} new emails'
                sync_log.save(update_fields=['message'])
                
                sync_log.status = 'success'
                
                # History Event: Success completion  
                SyncHistoryEvent.objects.create(
                    sync_log=sync_log,
                    event_type='finish',
                    message=f'✅ Successfully synced {emails_processed} new emails (skipped {already_synced} existing)',
                    emails_processed=emails_processed,
                    emails_added=emails_added,
                    emails_updated=emails_updated
                )
                
                # Update final message with completion
                sync_log.message = f'✅ Successfully synced {emails_processed} new emails (skipped {already_synced} existing)'
            
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            # Update account stats
            self.gmail_account.last_sync_at = timezone.now()
            self.gmail_account.update_sync_stats(email_count=self.gmail_account.emails.count())
            
            logger.info(f"Incremental sync completed: {emails_processed} new emails processed")
            return sync_log
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            sync_log.status = 'error'
            sync_log.completed_at = timezone.now()
            sync_log.message = f'❌ Sync failed: {str(e)}'
            sync_log.error_details = str(e)
            sync_log.save()
            raise
    
    def sync_emails(self, query: str = "", max_emails: int = 1000) -> SyncLog:
        """
        Sync emails from Gmail to database with real-time progress updates
        Supports cancellation by checking sync_log status
        
        Args:
            query: Gmail search query
            max_emails: Maximum number of emails to sync
            
        Returns:
            SyncLog instance
        """
        if not self.gmail_account:
            raise ValueError("No Gmail account provided")
        
        # Create sync log
        sync_log = SyncLog.objects.create(
            gmail_account=self.gmail_account,
            status='started',
            message='Connecting to Gmail API...'
        )
        
        try:
            emails_processed = 0
            emails_added = 0
            emails_updated = 0
            errors_count = 0
            page_token = None
            batch_count = 0
            cancelled = False  # Track if sync was cancelled
            
            # Update: Connected
            sync_log.message = '✓ Connected to Gmail API. Retrieving emails...'
            sync_log.save(update_fields=['message'])
            
            while emails_processed < max_emails:
                # Check if sync has been cancelled
                if self._should_cancel_sync(sync_log.id):
                    logger.info(f"Sync {sync_log.id} cancelled by user, stopping...")
                    cancelled = True
                    sync_log.message = f'🛑 Sync cancelled by user. Progress saved: {emails_processed} emails processed'
                    sync_log.save(update_fields=['message'])
                    # Create history event
                    from .models import SyncHistoryEvent
                    SyncHistoryEvent.objects.create(
                        sync_log=sync_log,
                        event_type='cancel',
                        message=f'Sync cancelled by user at {emails_processed} emails',
                        emails_processed=emails_processed,
                        emails_added=emails_added,
                        emails_updated=emails_updated
                    )
                    break
                
                try:
                    # Get batch of emails
                    batch_count += 1
                    batch_size = min(100, max_emails - emails_processed)
                    
                    # Update: Fetching batch
                    sync_log.message = f'📥 Fetching batch {batch_count} ({batch_size} emails)...'
                    sync_log.save(update_fields=['message'])
                    # Create history event
                    from .models import SyncHistoryEvent
                    SyncHistoryEvent.objects.create(
                        sync_log=sync_log,
                        event_type='fetch',
                        message=f'Fetching batch {batch_count} ({batch_size} emails)',
                        emails_processed=emails_processed,
                        batch_number=batch_count
                    )
                    
                    email_list, page_token = self.get_emails(
                        query=query,
                        max_results=batch_size,
                        page_token=page_token
                    )
                    
                    if not email_list:
                        break
                    
                    # Update: Processing batch
                    sync_log.message = f'⚙️ Processing {len(email_list)} emails from batch {batch_count}...'
                    sync_log.save(update_fields=['message'])
                    # Create history event
                    SyncHistoryEvent.objects.create(
                        sync_log=sync_log,
                        event_type='process',
                        message=f'Processing {len(email_list)} emails from batch {batch_count}',
                        emails_processed=emails_processed,
                        batch_number=batch_count
                    )
                    
                    # Process each email
                    for idx, email_data in enumerate(email_list, 1):
                        # Check for cancellation every 10 emails
                        if idx % 10 == 0 and self._should_cancel_sync(sync_log.id):
                            logger.info(f"Sync {sync_log.id} cancelled during email processing, stopping...")
                            cancelled = True
                            sync_log.message = f'🛑 Sync cancelled. Progress saved: {emails_processed} emails processed'
                            sync_log.save(update_fields=['message'])
                            # Create history event
                            from .models import SyncHistoryEvent
                            SyncHistoryEvent.objects.create(
                                sync_log=sync_log,
                                event_type='cancel',
                                message=f'Sync cancelled during processing at {emails_processed} emails',
                                emails_processed=emails_processed,
                                emails_added=emails_added,
                                emails_updated=emails_updated,
                                batch_number=batch_count
                            )
                            break
                        
                        try:
                            email_obj, created = self._save_email_to_db(email_data)
                            if created:
                                emails_added += 1
                            else:
                                emails_updated += 1
                            emails_processed += 1
                            
                            # Update progress every 10 emails
                            if idx % 10 == 0:
                                sync_log.emails_processed = emails_processed
                                sync_log.emails_added = emails_added
                                sync_log.emails_updated = emails_updated
                                sync_log.message = f'⚙️ Processed {emails_processed} emails ({emails_added} new, {emails_updated} updated)'
                                sync_log.save(update_fields=['emails_processed', 'emails_added', 'emails_updated', 'message'])
                                
                        except Exception as e:
                            errors_count += 1
                            logger.error(f"Failed to save email {email_data.get('gmail_id')}: {e}")
                    
                    # Update after batch completion (skip if cancelled to avoid +9 bug)
                    if not cancelled:
                        sync_log.emails_processed = emails_processed
                        sync_log.emails_added = emails_added
                        sync_log.emails_updated = emails_updated
                        sync_log.errors_count = errors_count
                        sync_log.message = f'✓ Batch {batch_count} complete. Total: {emails_processed} emails'
                        sync_log.save(update_fields=['emails_processed', 'emails_added', 'emails_updated', 'errors_count', 'message'])
                        # Create history event
                        from .models import SyncHistoryEvent
                        SyncHistoryEvent.objects.create(
                            sync_log=sync_log,
                            event_type='complete',
                            message=f'Batch {batch_count} complete: {len(email_list)} emails processed',
                            emails_processed=emails_processed,
                            emails_added=emails_added,
                            emails_updated=emails_updated,
                            batch_number=batch_count
                        )
                    
                    # Stop if no more pages
                    if not page_token:
                        break
                        
                except Exception as e:
                    errors_count += 1
                    logger.error(f"Error in sync batch: {e}")
                    sync_log.errors_count = errors_count
                    sync_log.save(update_fields=['errors_count'])
                    break
            
            # Update sync log
            sync_log.emails_processed = emails_processed
            sync_log.emails_added = emails_added
            sync_log.emails_updated = emails_updated
            sync_log.errors_count = errors_count
            
            # Determine status
            if errors_count > 0 and emails_processed > 0:
                status = 'partial'
                message = f"Synced with {errors_count} errors"
            elif errors_count > 0:
                status = 'error'
                message = "Sync failed with errors"
            else:
                status = 'success'
                message = f"Successfully synced {emails_processed} emails"
            
            sync_log.mark_completed(status, message)
            
            # Update account sync stats
            self.gmail_account.update_sync_stats(email_count=self.gmail_account.emails.count())
            
            logger.info(f"Sync completed for {self.gmail_account.email_address}: {message}")
            return sync_log
            
        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            sync_log.mark_completed('error', error_msg, str(e))
            logger.error(f"Sync failed for {self.gmail_account.email_address}: {e}")
            raise
    
    def _save_email_to_db(self, email_data: Dict) -> Tuple[EmailMessage, bool]:
        """Save email data to database"""
        # Remove attachments from email_data for model creation
        attachments = email_data.pop('attachments', [])
        
        # Create or update email
        email_obj, created = EmailMessage.objects.update_or_create(
            gmail_id=email_data['gmail_id'],
            defaults={
                **email_data,
                'gmail_account': self.gmail_account
            }
        )
        
        # Save attachments
        if attachments and created:  # Only save attachments for new emails
            for attachment_data in attachments:
                EmailAttachment.objects.create(
                    email=email_obj,
                    **attachment_data
                )
        
        return email_obj, created