"""Clean up stuck/ghost syncs that are older than 10 minutes."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from gmail_integration.models import SyncLog
from django.utils import timezone
from datetime import timedelta

cutoff = timezone.now() - timedelta(minutes=10)
stuck_syncs = SyncLog.objects.filter(status='started', started_at__lt=cutoff)

count = stuck_syncs.count()
print(f'Found {count} stuck syncs older than 10 minutes')

for sync in stuck_syncs:
    original_message = sync.message
    sync.status = 'interrupted'
    sync.message = f'⚠️ Sync interrupted - no progress for 10+ minutes (stuck at: {original_message})'
    sync.completed_at = sync.started_at + timedelta(minutes=10)
    sync.save()
    print(f'  - Sync {sync.id}: marked as interrupted (was at: {original_message})')

print(f'\nCleaned up {count} stuck syncs')
