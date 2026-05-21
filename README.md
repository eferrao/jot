# jot.

a simple to-do app — capture-first, paper-feeling. one html file, no build step, no backend.

## live

https://eferrao.github.io/jot/

## design intent

the goal isn't to win against asana or notion. it's to win against a paper notebook. so:

- **capture is the only fast path.** input is autofocused on load. enter saves. no required fields. no category picker.
- **two zones, soft separation.** work and personal, one toggle (or ⌘1 / ⌘2). everything else lives inside a zone.
- **mess-tolerant.** items can have a thumbnail (paste a sketch right into the capture box) or a notes blurb. or just be a one-liner.
- **trust.** delete has undo. nothing autosaves to a server you don't control — your data lives in your browser's localStorage.
- **paper feel.** warm off-white, dashed rule, serif title, subtle dotted texture. not a saas dashboard.

## keyboard

- `enter` — save the current capture
- `⌘1` / `⌘2` — switch zones
- `/` — focus the capture field from anywhere
- paste an image directly into the capture field — it becomes an item with a thumbnail

## editing

everything is in `index.html` — one file, vanilla js, no framework, no build. open it locally in any browser, or edit on github and the live version updates within a minute (github pages auto-deploys from `main`).

things worth playing with if you want to tweak it:
- color palette: the css `:root` block at the top (`--paper`, `--ink`, etc.)
- the seed/sample items: the `seed` object in the script
- the zone labels ("work" / "personal"): in the html header
- font: the `h1` rule (currently iowan old style with georgia fallback)

## known limitations (v1)

- data lives only in this browser. no sync between devices, no backup. if you clear browser data, items go.
- no real drawing surface — only image attachment.
- no due dates, reminders, recurring tasks, sub-tasks.
- accessibility needs a pass (contrast, touch target sizes).

built as a starting point, not a finished product. open an issue or just edit it.
