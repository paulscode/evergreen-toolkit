# Customize Example Names

This toolkit uses example names (**Alice**, **Bob**, **Eve**) throughout. Replace these with your actual household names before production use.

## Quick Search

> **Note:** The bulk `sed` commands in this file could modify this file itself, since it contains example names as documentation. Exclude this file from bulk replacements: add `--exclude=docs/NAME-CUSTOMIZATION.md` to `grep` commands and `-not -path './docs/NAME-CUSTOMIZATION.md'` to `find` commands.

```bash
cd ~/.openclaw/workspace
# Use word-boundary matching (\b) to avoid false positives (e.g., "Every", "event")
grep -rP '\bAlice\b|\bBob\b|\bEve\b' --include="*.md" --include="*.py" --include="*.json" . | head -20
```

> **macOS note:** The `-P` flag requires GNU grep. On macOS, install via `brew install grep` and use `ggrep -P` instead, or use `grep -E` with equivalent patterns.

## What to Replace (Both Capitalized and Lowercase)

| Example | Replace With | Files Affected |
|---------|--------------|----------------|
| `Alice` / `alice` | Your user's name / your-user-id | Docs, paths, `--user-id` args |
| `Bob` / `bob` | Your user's name / your-user-id | Docs, paths, `--user-id` args |
| `Eve` / `eve` | Your agent's name / your-agent-id | Scripts, docs, collections |
| `<agent>-memories` | Your agent's Qdrant collection name | Set via `QDRANT_COLLECTION` env var |
| `+11234567890` | Your phone numbers | Config examples |
| `+12345678901` | Your phone numbers | Config examples |

⚠️ **IMPORTANT:** Don't blindly replace! Examine each instance in context first.

**Examples requiring careful review:**
- `"Alice is Bob's wife"` → May not match your relationships! → **Edit or remove**
- `"Bob prefers dark mode"` → Transfer the preference if accurate → **Edit with real preference**
- `"Alice called Bob"` → Generic example → **Safe to replace**
- `"Eve said..."` in example snippets → **Safe to replace**

## Step 1: Find All Instances (Don't Replace Yet!)

```bash
cd ~/.openclaw/workspace
# Use word-boundary matching (\b) to avoid false positives (e.g., "Every", "event")
grep -rP '\bAlice\b|\bBob\b|\bEve\b' --include="*.md" --include="*.py" --include="*.json" . | head -20
```

Review the output to understand where example names appear in your installation.

## ⚠️ CRITICAL: Review Before Replacing!

**Don't blindly replace all instances!** Some examples contain specific claims that may not apply to your household.

**For each match from Step 1, categorize:**

### ✅ SAFE TO REPLACE (Generic Examples)
- Command examples: `--user-id alice` → `--user-id <your-user-id>`
- Path examples: `/home/alice/.openclaw/` → `/home/<your-user>/.openclaw/`
- Collection names: `<agent>-memories` → `your_agent_memories`
- Generic statements: "Alice uses WhatsApp" → "<User> uses WhatsApp"
- Placeholder text: "Contact Alice at +11234567890" → "Contact <User> at <your-number>"
- Code comments: `"Bob: Should I use Redis?"` → `"<user>: Should I use Redis?"`

### ⚠️ EDIT CAREFULLY (Specific Claims - May Not Apply)
- **Relationships:** "Alice is Bob's wife" → May not match your household → **Remove or rewrite**
- **Preferences:** "Bob prefers dark mode" → Only keep if TRUE → **Edit with real preference or remove**
- **Personal facts:** "Alice has 3 grandkids" → Replace with YOUR facts → **Edit or remove**
- **Historical context:** "Bob decided on Redis for caching" → Genericize → **Rewrite as "The user decided..."**
- **Behavioral examples:** "Alice checks messages daily" → May not be true → **Remove or verify**

### ❌ REMOVE ENTIRELY (Template Artifacts)
- Instructions to user: "Replace Alice with your user's name"
- Meta-comments: "Example: Alice said..."
- Obvious placeholders: "Your Name", "yourdomain.com"

**Example Workflow:**
```bash
# 1. Find an instance
grep -n "Alice is Bob's wife" docs/MEMORY-INTEGRATION.md

# 2. Open the file and review context
nano docs/MEMORY-INTEGRATION.md

# 3. Decide: Is this relationship accurate for your household?
#    - YES: Keep as-is (rare)
#    - NO: Edit to reflect YOUR relationships or remove entirely

# 4. Save and continue
```

**Recommendation:** For relationship/fact examples, use vague language instead:
- ❌ "Alice is Bob's wife" (specific, may be wrong)
- ✅ "User A lives with User B" (generic, always safe)
- ✅ "The primary user (Alice) asked the technical user (Bob)..." → "The household members discussed..."

---

## Step 2: Bulk Replace with sed

> **Important:** Exclude this file (`docs/NAME-CUSTOMIZATION.md`) from bulk replacements — it documents the example names and would be mangled by `sed`.

**Replace capitalized names (docs, display text):**
```bash
# Markdown files - capitalized (replace YourUser1/YourUser2/YourAgent with actual names)
# Uses \< and \> for word boundaries (GNU sed). On macOS, use: brew install gnu-sed
find . -name "*.md" -not -path './docs/NAME-CUSTOMIZATION.md' -exec sed -i 's/\<Alice\>/YourUser1/g' {} \;
find . -name "*.md" -not -path './docs/NAME-CUSTOMIZATION.md' -exec sed -i 's/\<Bob\>/YourUser2/g' {} \;
find . -name "*.md" -not -path './docs/NAME-CUSTOMIZATION.md' -exec sed -i 's/\<Eve\>/YourAgent/g' {} \;
```

**Replace lowercase names (user IDs, paths, code):**
```bash
# Markdown files - lowercase (user IDs in paths, arguments)
find . -name "*.md" -not -path './docs/NAME-CUSTOMIZATION.md' -exec sed -i 's/\<alice\>/<your-user-id>/g' {} \;
find . -name "*.md" -not -path './docs/NAME-CUSTOMIZATION.md' -exec sed -i 's/\<bob\>/<your-user-id>/g' {} \;
find . -name "*.md" -not -path './docs/NAME-CUSTOMIZATION.md' -exec sed -i 's/\<eve\>/<your-agent-id>/g' {} \;

# Python files - agent name and collection
find . -name "*.py" -exec sed -i 's/\<Eve\>/YourAgent/g' {} \;
find . -name "*.py" -exec sed -i 's/\<eve\>/<your-agent-id>/g' {} \;
find . -name "*.py" -exec sed -i 's/<agent>-memories/<your-agent-id>_memories/g' {} \;

# Config files (YAML, JSON, shell scripts)
find . \( -name "*.yaml" -o -name "*.json" -o -name "*.sh" \) \
  -exec sed -i 's/\<alice\>/<your-user-id>/g' {} \;
find . \( -name "*.yaml" -o -name "*.json" -o -name "*.sh" \) \
  -exec sed -i 's/\<bob\>/<your-user-id>/g' {} \;
find . \( -name "*.yaml" -o -name "*.json" -o -name "*.sh" \) \
  -exec sed -i 's/\<eve\>/<your-agent-id>/g' {} \;
```

## Step 3: Verify All Replacements
```bash
# Check for any remaining references (both cases, with word boundaries)
grep -rP '\bAlice\b|\balice\b|\bBob\b|\bbob\b|\bEve\b|\beve\b' --include="*.md" --include="*.py" .

# Should only find intentional uses
# If you find actual name references, replace them
```

**Tip:** Use word boundaries (`\<` and `\>`) in GNU sed to avoid replacing substrings (e.g., "believe" contains "eve"). On macOS, install GNU sed via `brew install gnu-sed` and use `gsed` instead of `sed`.

---

## Key Files to Manually Review

- `memory/MULTI-USER-GUIDE.md` - User profiles, phone numbers
- `memory/curator_prompts/base.md` - AI curator prompt (speaker labels)
- `memory/scripts/log_activity.py` - AGENT_NAME (reads from env var)
- `docs/MEMORY-INTEGRATION.md` - User mapping table
- `config/crontab.sample` - Paths, user IDs

**After customizing:** Run `python3 scripts/validate-customization.py` to verify all placeholders and example names have been replaced. You can also re-run the grep command above for a manual check.
