# Sync All Parameter Fix

## Problem
User reported: "sync all is only doing 1000 emails" despite implementing the sync all checkbox feature.

## Root Cause
The sync all checkbox was sending `{ sync_all: true }` as **JSON** in the request body, but the Django view was trying to read from `request.POST`, which is **only populated for form-encoded data** (Content-Type: application/x-www-form-urlencoded).

### Code Flow Before Fix:
1. **JavaScript** (account_detail.html line 472):
   ```javascript
   const requestBody = syncAll ? JSON.stringify({ sync_all: true }) : JSON.stringify({});
   fetch(url, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: requestBody
   });
   ```

2. **Django View** (views.py line 318):
   ```python
   sync_all = request.POST.get('sync_all', 'false').lower() == 'true'
   ```
   ❌ **request.POST is empty when Content-Type is application/json!**

3. Result: `sync_all` was always `'false'`, so `max_emails` was always 1000 (the default)

## Solution
Modified the view to detect JSON requests and parse the body accordingly:

### views.py (lines 316-332):
```python
try:
    # Parse request data (supports both JSON and form data)
    if request.content_type == 'application/json':
        import json
        data = json.loads(request.body)
    else:
        data = request.POST
    
    # Get sync parameters
    query = data.get('query', '')
    max_emails_param = data.get('max_emails', '1000')
    sync_all = str(data.get('sync_all', 'false')).lower() == 'true'
    
    # Handle "sync all" option
    if sync_all:
        max_emails = 999999  # Effectively unlimited
        logger.info(f"🚀 SYNC ALL enabled: max_emails set to {max_emails}")
    else:
        max_emails = int(max_emails_param)
        logger.info(f"📊 Standard sync: max_emails set to {max_emails}")
```

## Debug Logging Added
Added comprehensive logging throughout the sync chain to track the `max_emails` parameter:

1. **views.py** `sync_emails_ajax`:
   - Logs when sync all is enabled: `"🚀 SYNC ALL enabled: max_emails set to 999999"`
   - Logs standard sync: `"📊 Standard sync: max_emails set to {value}"`

2. **views.py** `run_sync_in_background`:
   - `"[THREAD START] Background sync started for account X with max_emails=999999"`
   - `"[THREAD] Calling sync_emails_incremental with max_emails=999999"`

3. **services.py** `sync_emails_incremental`:
   - `"[SERVICE] sync_emails_incremental called with max_emails=999999"`

4. **services.py** `get_new_message_ids`:
   - `"[SERVICE] get_new_message_ids called with max_messages=999999"`

5. **services.py** `get_all_message_ids`:
   - `"[SERVICE] get_all_message_ids called with max_messages=999999"`

## Testing Instructions
1. Start Django server: `python manage.py runserver`
2. Go to Gmail account detail page
3. Click sync options dropdown → Check "Sync ALL emails"
4. Click "Sync Now"
5. Check Django logs (logs/django.log) for the logging chain:
   ```
   🚀 SYNC ALL enabled: max_emails set to 999999
   [THREAD START] Background sync started for account X with max_emails=999999
   [THREAD] Calling sync_emails_incremental with max_emails=999999
   [SERVICE] sync_emails_incremental called with max_emails=999999
   [SERVICE] get_new_message_ids called with max_messages=999999
   [SERVICE] get_all_message_ids called with max_messages=999999
   ```

## Expected Behavior
- **With sync all checked**: Should sync ALL emails in the account (999,999 max)
- **Without sync all checked**: Should sync default 1000 emails
- **Logs confirm**: Parameter values at each step

## Alternative Solutions Considered
1. **Change JavaScript to send form data** - Would work but less clean
2. **Change to always use JSON** - Current solution, more flexible
3. **Add query parameter** - Less secure, harder to test

## Commit
- Commit: `eaee164`
- Branch: `feature/gmail-integration`
- Status: ✅ Committed and pushed

## Next Steps
1. User should test the sync all feature
2. Verify logs show correct parameter values
3. Confirm all emails are synced (not just 1000)
4. If issue persists, logs will show where parameter is lost
