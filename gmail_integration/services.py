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
            # Refresh token if expired
            if self._credentials.expired and self._credentials.refresh_token:
                logger.info("Token expired, refreshing...")
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
        Parse Gmail message into structured data
        
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
            
            # Parse date
            date_str = headers.get('Date', '')
            if date_str:
                try:
                    email_data['sent_date'] = parsedate_to_datetime(date_str)
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
    
    def sync_emails(self, query: str = "", max_emails: int = 1000) -> SyncLog:
        """
        Sync emails from Gmail to database
        
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
            status='started'
        )
        
        try:
            emails_processed = 0
            emails_added = 0
            emails_updated = 0
            errors_count = 0
            page_token = None
            
            while emails_processed < max_emails:
                try:
                    # Get batch of emails
                    batch_size = min(100, max_emails - emails_processed)
                    email_list, page_token = self.get_emails(
                        query=query,
                        max_results=batch_size,
                        page_token=page_token
                    )
                    
                    if not email_list:
                        break
                    
                    # Process each email
                    for email_data in email_list:
                        try:
                            email_obj, created = self._save_email_to_db(email_data)
                            if created:
                                emails_added += 1
                            else:
                                emails_updated += 1
                            emails_processed += 1
                        except Exception as e:
                            errors_count += 1
                            logger.error(f"Failed to save email {email_data.get('gmail_id')}: {e}")
                    
                    # Stop if no more pages
                    if not page_token:
                        break
                        
                except Exception as e:
                    errors_count += 1
                    logger.error(f"Error in sync batch: {e}")
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