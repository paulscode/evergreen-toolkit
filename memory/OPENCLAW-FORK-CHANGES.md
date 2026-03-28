# 🔧 OpenClaw Fork Changes for Multi-User Isolation

> **⚠️ OPTIONAL — Advanced Enhancement.** These changes apply only if you maintain a fork of the OpenClaw TypeScript gateway **and** want end-to-end user isolation at the gateway level. **Most users do NOT need this file.** The toolkit works without these changes; user isolation is handled at the Python script level via `--user-id` arguments and per-user Redis keys. Skip this document unless you are forking the OpenClaw gateway.

> **⚠️ File paths below are OpenClaw gateway files, NOT evergreen-toolkit files.** The TypeScript files referenced in this document (e.g., `plugins/types.ts`, `openclaw-tools.ts`) are part of the OpenClaw gateway codebase. Do not look for them in the evergreen-toolkit directory.

This document describes the TypeScript changes needed in your OpenClaw gateway fork to enable end-to-end multi-user memory isolation. These changes ensure that the AI knows **who** it's talking to and uses the correct memory space for each person.

---

## Overview

Multi-user isolation requires changes at three layers:

```
┌─────────────────────────────────────────────────────┐
│ 1. Identity Resolution                              │
│    Phone number → user_id via mapping file          │
├─────────────────────────────────────────────────────┤
│ 2. Memory Tool Wiring                               │
│    Pass --user-id to all Python memory scripts      │
├─────────────────────────────────────────────────────┤
│ 3. System Prompt Isolation                          │
│    Instruct AI to maintain per-user mental models   │
└─────────────────────────────────────────────────────┘
```

---

## 1. User-Phone Mapping File

Create `~/.openclaw/user-phone-mapping.json`:

```json
{
  "+11234567890": "alice",
  "+12345678901": "bob"
}
```

This file is read by the gateway at runtime to resolve caller identity.

---

## 2. Memory Tool Changes (`src/agents/tools/memory-tool.ts`)

### 2a. Add Phone-to-User Resolution

Add a function that reads the mapping file and resolves a phone number to a user_id:

```typescript
import { readFileSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

function resolveUserIdFromE164(e164: string | undefined): string | undefined {
  if (!e164) return undefined;
  try {
    const mappingPath = join(homedir(), '.openclaw', 'user-phone-mapping.json');
    const mapping = JSON.parse(readFileSync(mappingPath, 'utf-8'));
    return mapping[e164] || undefined;
  } catch {
    return undefined;
  }
}
```

### 2b. Wire user_id into Memory Search

In the `memory_search` tool handler, resolve the caller's identity and pass `--user-id` to the search script:

```typescript
// Inside the memory_search tool execution:
const senderE164 = context?.senderE164; // passed through plugin context
const userId = resolveUserIdFromE164(senderE164);

const args = [scriptPath, query, '--limit', '5', '--json'];
if (userId) {
  args.push('--user-id', userId);
}
```

### 2c. Wire user_id into Memory Store

Similarly, when storing memories via the `storeNote` tool:

```typescript
const args = [scriptPath, noteText, '--tags', tags];
if (userId) {
  args.push('--user-id', userId);
}
```

---

## 3. Voice Agent Changes (`realtime-full-handler.ts` or equivalent)

### 3a. Pass senderE164 Through Plugin Context

The voice agent receives the caller's phone number. Pass it through the plugin context chain so memory tools can access it:

```typescript
// In your plugin types (plugins/types.ts or equivalent):
interface PluginContext {
  // ... existing fields
  senderE164?: string;
}

// When creating the voice session context:
const context: PluginContext = {
  // ... existing context
  senderE164: incomingCallFrom, // The E.164 phone number of the caller
};
```

### 3b. Add User Isolation to Voice System Prompt

Add a section to the voice agent's system prompt that instructs it to maintain per-user mental models:

```typescript
const userIsolationPrompt = `
## USER ISOLATION (Theory of Mind)
You support a multi-user household. Each person you talk to has their own
memory space, personality, and relationship context.

When searching or storing memories, the system automatically uses the
correct user_id based on the caller's phone number. Your job is to:

1. Remember which person you're currently speaking with
2. Use their name naturally in conversation
3. Don't confuse one person's preferences, history, or relationships with another's
4. If someone asks about another household member, respond based on
   what YOU know about that relationship — not the other person's private memories
`;
```

---

## 4. Base Agent Changes (`system-prompt.ts`)

For the text/chat agent, add similar isolation instructions to the base system prompt:

```typescript
const userIsolationSection = `
## USER ISOLATION
This is a multi-user household system. When you retrieve memories,
the results are automatically filtered to the current user. Maintain
separate mental models for each person:

- Don't assume what one user knows based on conversations with another
- Respect privacy boundaries between users
- Use names naturally when referring to household members
`;
```

---

## 5. Context Chain Wiring

The `senderE164` value needs to flow through the OpenClaw plugin system:

```
Incoming call/message
  → Gateway receives phone number
    → Plugin context includes senderE164
      → Tools receive context
        → memory-tool.ts calls resolveUserIdFromE164()
          → Python scripts get --user-id flag
            → Qdrant filters by user_id
```

### Files to Modify

| File | Change |
|------|--------|
| `plugins/types.ts` | Add `senderE164?: string` to context interface |
| `openclaw-tools.ts` | Pass `senderE164` from session to tool context |
| `pi-tools.ts` | Same wiring for Pi tools |
| `memory-core/index.ts` | Same wiring for memory core |
| `memory-tool.ts` | Add `resolveUserIdFromE164()`, pass `--user-id` to scripts |
| `memory-service.ts` | Pass `--user-id` to `hybrid_search.py` and `store_memory.py` |
| `realtime-full-handler.ts` | Add USER ISOLATION section to voice prompt |
| `system-prompt.ts` | Add USER ISOLATION section to base prompt |

---

## 6. Testing the Integration

### Test 1: Identity Resolution

```bash
# Verify the mapping file is readable
node -e "
const fs = require('fs');
const path = require('path');
const mapping = JSON.parse(fs.readFileSync(
  path.join(require('os').homedir(), '.openclaw/user-phone-mapping.json'), 'utf-8'
));
console.log('Mapping:', mapping);
"
```

### Test 2: End-to-End Voice Call

1. Call from Alice's phone → system should resolve to "alice"
2. Ask "Remember that I love morning walks"
3. Call from Bob's phone → system should resolve to "bob"
4. Ask "What does my wife like to do?" (should relate to Alice's memories if relationship is stored)
5. Ask "Do I like morning walks?" → should say "I don't have that recorded for you" (Bob-isolated)

### Test 3: Memory Isolation Verification

```bash
# Check that Alice's memory has user_id=alice
curl -s http://localhost:6333/collections/<agent>-memories/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"filter":{"must":[{"key":"user_id","match":{"value":"alice"}}]},"limit":5,"with_payload":true}' | \
  python3 -m json.tool

# Verify Bob can't see Alice's memories
python3 search_memories.py "morning walks" --user-id bob
# Should return empty or unrelated results
```

---

## Notes

- **Backwards compatible**: If `--user-id` is not passed, scripts work as before (no filtering)
- **Phone mapping is optional**: For web/chat users, user_id can be passed through session metadata instead
- **Hot-reloadable**: The mapping file is read on each request, so changes take effect immediately without restarting the gateway
- **No shared collection splitting**: All users share one Qdrant collection, isolated by payload filters. This is simpler to manage and allows future cross-user features

---

For the Python script changes, see [MULTI-USER-GUIDE.md](MULTI-USER-GUIDE.md).
