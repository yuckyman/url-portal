# iPhone Shortcut: WM Portal

## Overview

The iPhone shortcut acts as the glue layer between QR code scans and the yuckbox portal server.

## Shortcut Flow

1. **Trigger**: URL scheme or QR code scan
2. **Parse URL**: Extract portal ID from `https://yuckbox/wm/p/<id>`
3. **Get Portal Info**: Call `GET https://yuckbox/wm/p/<id>`
4. **Execute Action**: Call `POST https://yuckbox/wm/act` with portal_id and action
5. **Display Result**: Show success/error message to user

## Shortcut Steps

### Step 1: Get Input
- **Action**: "Get Contents of URL"
- **Input**: The scanned URL (from QR code or URL scheme)

### Step 2: Extract Portal ID
- **Action**: "Get Text from Input"
- **Action**: "Match Text" with pattern: `wm/p/([a-z0-9]{6,12})`
- **Action**: "Get Group from Matched Text" (group 1)

### Step 3: Get Portal Configuration
- **Action**: "Get Contents of URL"
- **URL**: `https://yuckbox/wm/p/{portal_id}` (replace {portal_id} with extracted ID)
- **Method**: GET
- **Headers**: None needed for now

### Step 4: Parse Response
- **Action**: "Get Dictionary from Input"
- **Action**: "Get Value for" key: "action"

### Step 5: Execute Action
- **Action**: "Get Contents of URL"
- **URL**: `https://yuckbox/wm/act`
- **Method**: POST
- **Headers**: 
  - `Content-Type: application/json`
- **Request Body** (JSON):
```json
{
  "portal_id": "{portal_id}",
  "action": "{action}"
}
```

### Step 6: Handle Response
- **Action**: "Get Dictionary from Input"
- **Action**: "If" success == true
  - **Then**: Show notification "Daily note created successfully!"
  - **Else**: Show notification "Error: {error message}"

## Example: Daily Note Portal

For the "dly" portal specifically:

1. Scan QR code with URL: `https://yuckbox/wm/p/dly`
2. Shortcut extracts "dly" as portal_id
3. Calls `GET /wm/p/dly` → gets `{"action": "open_daily"}`
4. Calls `POST /wm/act` with:
   ```json
   {
     "portal_id": "dly",
     "action": "open_daily"
   }
   ```
5. Server creates daily note, commits, pushes
6. Returns success response

## Testing

To test without QR codes:
- Use "Run Shortcut" action with URL input
- Or create a test URL: `https://yuckbox/wm/p/dly`

## Error Handling

The shortcut should handle:
- Network errors (yuckbox unreachable)
- Invalid portal IDs
- Action execution failures
- Display appropriate error messages to the user

