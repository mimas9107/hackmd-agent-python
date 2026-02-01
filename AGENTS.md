# AGENTS.md - AI Agent Integration Guide

This document provides instructions for AI agents to effectively use the HackMD tools provided by this library.

## Overview

This library provides 6 HackMD tools that allow AI agents to manage notes on HackMD. All tools are async and return JSON-formatted strings.

## Available Tools

### 1. `hackmd_list_notes`

**Purpose:** List all notes belonging to the authenticated user.

**Input:** None required

**Output:** JSON array of note objects with metadata (id, title, createdAt, updatedAt, etc.)

**Example Usage:**
```json
{
  "name": "hackmd_list_notes",
  "input": {}
}
```

**When to Use:**
- User asks to see their notes
- Need to find a note ID for subsequent operations
- Checking what notes exist before creating a new one

---

### 2. `hackmd_read_note`

**Purpose:** Read the full content of a specific note.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `noteId` | string | Yes | The unique ID of the note |

**Output:** JSON object with note metadata and `content` field containing the markdown

**Example Usage:**
```json
{
  "name": "hackmd_read_note",
  "input": {
    "noteId": "abc123xyz"
  }
}
```

**When to Use:**
- User asks to read/view a note
- Need to check current content before updating
- Analyzing note content for summarization

---

### 3. `hackmd_create_note`

**Purpose:** Create a new note on HackMD.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes | The title of the new note |
| `content` | string | Yes | The markdown content |
| `readPermission` | string | No | `"owner"`, `"signed_in"`, or `"guest"` |
| `writePermission` | string | No | `"owner"`, `"signed_in"`, or `"guest"` |

**Output:** JSON object with the created note's metadata including `id` and `publishLink`

**Example Usage:**
```json
{
  "name": "hackmd_create_note",
  "input": {
    "title": "Meeting Notes - 2024-02-01",
    "content": "# Meeting Notes\n\n## Attendees\n- Alice\n- Bob\n\n## Action Items\n- [ ] Follow up on project timeline"
  }
}
```

**When to Use:**
- User explicitly asks to create a new note
- Saving generated content (plans, summaries, reports)
- Documenting task results

**Best Practices:**
- Always use descriptive titles
- Format content with proper markdown headings
- Include date in title if relevant

---

### 4. `hackmd_update_note`

**Purpose:** Update the content of an existing note.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `noteId` | string | Yes | The unique ID of the note |
| `content` | string | Yes | The new markdown content |
| `readPermission` | string | No | `"owner"`, `"signed_in"`, or `"guest"` |
| `writePermission` | string | No | `"owner"`, `"signed_in"`, or `"guest"` |

**Output:** JSON object with updated note metadata

**Example Usage:**
```json
{
  "name": "hackmd_update_note",
  "input": {
    "noteId": "abc123xyz",
    "content": "# Updated Content\n\nThis note has been updated."
  }
}
```

**When to Use:**
- User asks to modify an existing note
- Appending new content to a note
- Fixing or updating information

**Best Practices:**
- Read the note first if you need to preserve existing content
- Warn user before overwriting content

---

### 5. `hackmd_delete_note`

**Purpose:** Permanently delete a note.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `noteId` | string | Yes | The unique ID of the note |

**Output:** JSON object with `{ "success": true, "message": "Note deleted" }`

**Example Usage:**
```json
{
  "name": "hackmd_delete_note",
  "input": {
    "noteId": "abc123xyz"
  }
}
```

**When to Use:**
- User explicitly asks to delete a note
- Cleaning up temporary notes

**Best Practices:**
- Always confirm with user before deleting
- This action cannot be undone

---

### 6. `hackmd_search_notes`

**Purpose:** Search notes by title keyword.

**Input:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `keyword` | string | Yes | The keyword to search for |

**Output:** JSON array of matching note objects

**Example Usage:**
```json
{
  "name": "hackmd_search_notes",
  "input": {
    "keyword": "meeting"
  }
}
```

**When to Use:**
- User asks to find a note by name
- Looking for notes related to a topic
- Before creating a note, check if similar exists

---

## Workflow Recommendations

### Creating a Note for Task Results

1. Generate the content
2. Call `hackmd_create_note` with a descriptive title
3. Return the `publishLink` to the user

### Updating an Existing Note

1. Use `hackmd_search_notes` or `hackmd_list_notes` to find the note
2. Use `hackmd_read_note` to get current content (if needed to preserve)
3. Use `hackmd_update_note` with the new content

### Organizing Notes

1. Use consistent title prefixes (e.g., "Meeting - ", "Project - ")
2. Include dates in titles for time-sensitive notes
3. Use markdown headers for structure

## Error Handling

All tools may return error responses in this format:
```json
{
  "error": "Error message here"
}
```

Common errors:
- `"noteId is required"` - Missing required parameter
- `"Note not found"` - Invalid note ID
- `"Unauthorized"` - Invalid API token

## Integration Example

```python
import asyncio
from hackmd_agent import create_hackmd_tools, process_message
import anthropic

async def main():
    client = anthropic.AsyncAnthropic()
    tools = create_hackmd_tools("your-token")

    # Process user request
    result = await process_message(
        client,
        tools,
        "Create a note with my project plan"
    )

    print(result.response)
    print("Tools used:", result.tools_used)

asyncio.run(main())
```

## Async Considerations

All tools in this Python version are async. When integrating:

```python
# Direct tool execution
result = await execute_tool(tools, "hackmd_list_notes", {})

# Or within an async context
async with asyncio.TaskGroup() as tg:
    task1 = tg.create_task(execute_tool(tools, "hackmd_list_notes", {}))
    task2 = tg.create_task(execute_tool(tools, "hackmd_read_note", {"noteId": "abc"}))
```

## Version

This document is for **hackmd-agent-python v1.0.0**.

See [CHANGELOG.md](./CHANGELOG.md) for version history.
