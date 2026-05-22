# jot — CLAUDE.md

Project context for AI-assisted development.

## Architecture

**Single-file app.** Everything — HTML, CSS, JS — lives in `index.html`. There is no build step, no bundler, no package.json. Open `index.html` directly in a browser to run.

## Dark Mode

Implemented via CSS variables. Light theme defined on `:root`, dark theme overrides on `html[data-theme="dark"]`.

Toggle logic is in the `<script>` block near the bottom of `index.html`. Theme persists to `localStorage` under key `jot.theme`.

## localStorage Schema

| Key | Description |
|-----|-------------|
| `jot.theme` | `"light"` or `"dark"` |
| `jot.v2` | Main app state (see below) |
| `jot.v1` | Legacy format — auto-migrated to v2 on first load |

### `jot.v2` structure
```json
{
  "zone": "work",
  "spotlight": {
    "work": { "text": "...", "done": false, "ts": 1234567890 },
    "personal": null
  },
  "items": {
    "work": [
      { "id": 1, "text": "...", "notes": "...", "img": null, "done": false, "ts": 1234567890 }
    ],
    "personal": []
  }
}
```

- `zone`: active tab (`"work"` | `"personal"`)
- `spotlight`: one pinned task per zone (or `null`)
- `items`: task lists per zone; each task has `id`, `text`, `notes`, `img` (data URL or null), `done`, `ts` (unix ms)

## Feature Set (as of feat/merge-the-board merge)

- **Two zones**: Work / Personal tabs
- **Spotlight**: one pinned/priority task per zone; promote any task to spotlight
- **Task list**: add, check off, expand notes, attach sketch image
- **Date stamps**: relative timestamps on tasks (e.g. "2 hours ago")
- **Clear done**: removes all completed tasks in the current zone
- **Export**: downloads `jot-YYYY-MM-DD.json` with full state
- **Dark mode**: toggle button in header; persists across sessions; respects OS preference on first load
- **Ripped-paper accent**: decorative CSS on zone divider

## Branch / PR Workflow

```
feature branch → PR → main
```

1. Branch off `main`
2. Test locally (open `index.html` in browser)
3. `git push -u origin <branch>`
4. Open PR targeting `main`

## Key File

- `index.html` — the entire app (~760 lines)
- `README.md` — user-facing docs
