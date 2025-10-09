"""
WebSocket consumers for real-time features.
Handles presence tracking, live updates, and family communication.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class PresenceConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for tracking user presence and broadcasting status updates.
    
    Handles:
    - User online/offline status
    - Last seen timestamps
    - Heartbeat pings
    - Broadcasting presence to family members
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.user = self.scope["user"]
        
        # Reject anonymous users
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Get user's family (primary family for now)
        self.family = await self.get_user_family()
        
        if not self.family:
            # User not in any family - close connection
            await self.close()
            return
        
        # Create family group name for broadcasting
        self.family_group_name = f"family_{self.family.id}"
        
        # Join family channel group
        await self.channel_layer.group_add(
            self.family_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Mark user as online in database
        await self.mark_user_online()
        
        # Broadcast to family that user is now online
        await self.channel_layer.group_send(
            self.family_group_name,
            {
                'type': 'presence_update',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_online': True,
                'last_seen': timezone.now().isoformat()
            }
        )
        
        # Send current family presence status to newly connected user
        await self.send_family_presence()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'family_group_name'):
            # Mark user as offline
            await self.mark_user_offline()
            
            # Broadcast to family that user is now offline
            await self.channel_layer.group_send(
                self.family_group_name,
                {
                    'type': 'presence_update',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_online': False,
                    'last_seen': timezone.now().isoformat()
                }
            )
            
            # Leave family channel group
            await self.channel_layer.group_discard(
                self.family_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages.
        
        Message types:
        - heartbeat: Keep connection alive and update last seen
        - page_change: Update current page user is viewing
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'heartbeat':
                # Update heartbeat timestamp
                current_page = data.get('page')
                await self.update_heartbeat(current_page)
                
                # Send acknowledgment
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat_ack',
                    'timestamp': timezone.now().isoformat()
                }))
            
            elif message_type == 'page_change':
                # User changed page/module
                current_page = data.get('page')
                await self.update_current_page(current_page)
                
                # Broadcast page change to family (for collaborative features)
                await self.channel_layer.group_send(
                    self.family_group_name,
                    {
                        'type': 'user_page_change',
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'page': current_page
                    }
                )
        
        except json.JSONDecodeError:
            # Invalid JSON - ignore
            pass

    async def presence_update(self, event):
        """
        Send presence update to WebSocket client.
        Called when another user in the family goes online/offline.
        """
        await self.send(text_data=json.dumps({
            'type': 'presence_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_online': event['is_online'],
            'last_seen': event['last_seen']
        }))

    async def user_page_change(self, event):
        """
        Send page change notification to WebSocket client.
        Used for collaborative viewing features.
        """
        # Don't send to the user who changed pages
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'user_page_change',
                'user_id': event['user_id'],
                'username': event['username'],
                'page': event['page']
            }))

    # Database operations (sync functions wrapped with database_sync_to_async)
    
    @database_sync_to_async
    def get_user_family(self):
        """Get user's primary family"""
        try:
            family_member = self.user.familymember_set.order_by('joined_at').first()
            return family_member.family if family_member else None
        except Exception:
            return None

    @database_sync_to_async
    def mark_user_online(self):
        """Mark user as online in database"""
        from accounts.models import UserPresence
        
        presence, created = UserPresence.objects.get_or_create(user=self.user)
        presence.mark_online(
            channel_name=self.channel_name,
            current_page=self.scope.get('path', '')
        )

    @database_sync_to_async
    def mark_user_offline(self):
        """Mark user as offline in database"""
        from accounts.models import UserPresence
        
        try:
            presence = UserPresence.objects.get(user=self.user)
            presence.mark_offline()
        except UserPresence.DoesNotExist:
            pass

    @database_sync_to_async
    def update_heartbeat(self, current_page=None):
        """Update user's heartbeat timestamp"""
        from accounts.models import UserPresence
        
        try:
            presence = UserPresence.objects.get(user=self.user)
            presence.update_heartbeat(current_page=current_page)
        except UserPresence.DoesNotExist:
            pass

    @database_sync_to_async
    def update_current_page(self, current_page):
        """Update user's current page"""
        from accounts.models import UserPresence
        
        try:
            presence = UserPresence.objects.get(user=self.user)
            presence.current_page = current_page
            presence.save(update_fields=['current_page', 'updated_at'])
        except UserPresence.DoesNotExist:
            pass

    @database_sync_to_async
    def get_family_presence_data(self):
        """Get presence data for all family members"""
        from accounts.models import UserPresence, FamilyMember
        
        family_members = FamilyMember.objects.filter(
            family=self.family
        ).select_related('user', 'user__presence')
        
        presence_data = []
        for member in family_members:
            try:
                presence = member.user.presence
                presence_data.append({
                    'user_id': member.user.id,
                    'username': member.user.username,
                    'full_name': member.user.get_full_name() or member.user.username,
                    'role': member.role,
                    'is_online': presence.is_online,
                    'last_seen': presence.last_seen.isoformat(),
                    'current_page': presence.current_page or ''
                })
            except UserPresence.DoesNotExist:
                # User has no presence record yet
                presence_data.append({
                    'user_id': member.user.id,
                    'username': member.user.username,
                    'full_name': member.user.get_full_name() or member.user.username,
                    'role': member.role,
                    'is_online': False,
                    'last_seen': member.joined_at.isoformat(),
                    'current_page': ''
                })
        
        return presence_data

    async def send_family_presence(self):
        """Send current presence status of all family members"""
        presence_data = await self.get_family_presence_data()
        
        await self.send(text_data=json.dumps({
            'type': 'family_presence',
            'members': presence_data
        }))
