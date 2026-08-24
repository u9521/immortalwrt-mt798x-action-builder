---
name: archive-agent-note
description: Use when auditing, superseding, or archiving mature or replaced Agent Notes into the frozen .agents/notes/archived/ tree, including updating inbound links.
---

# Archive Agent Notes

Use this skill to safely retire mature or superseded Agent Notes into the frozen archive tree (`.agents/notes/archived/`).

## Archival Criteria

An implemented Agent Note should be archived when:
1. **Fully Mature**: The decision has shipped, is stable, and its historical debate is unlikely to guide active design.
2. **Superseded**: A newer Agent Note has replaced the decision or mechanism.
3. **Never archive a `proposed/` note**: If a proposal is abandoned, move it to `rejected/` (with a reason) or delete it.

---

## Step-by-Step Archival Procedure

### 1. Identify Target Note
Locate the note under `.agents/notes/implemented/{class}/yyyy-mm-dd-topic.md`.

### 2. Move File to Archive Tree
Move the note into `.agents/notes/archived/{class}/yyyy-mm-dd-topic.md`.
```bash
mkdir -p .agents/notes/archived/<class>
mv .agents/notes/implemented/<class>/<file>.md .agents/notes/archived/<class>/<file>.md
```

### 3. Insert Archive Marker
In the archived markdown file, insert the `Archived: YYYY-MM-DD` timestamp immediately below `Status: implemented`:

```markdown
# Agent Note: <Title>

Status: implemented
Archived: 2026-03-31
```

### 4. Update Inbound References
Search across the codebase for links pointing to the old path:
- Update markdown links to point to the new location or superseding note.

### 5. Verify Integrity
Run the repository verification gate:
```bash
python3 scripts/gates/verify_agent_gates.py
```
Ensure zero broken links exist across the documentation and notes trees.
