# jot.

a simple to-do app — capture-first, paper-feeling. one html file, no build step, no backend.

now merged with [the-board](https://github.com/jocelynbaun/the-board) — adds a **spotlight** per zone so the "one thing that matters today" sits at the top, above everything else.

## live

https://eferrao.github.io/jot/

## what's in it

- **spotlight at the top.** the single most important thing for the current zone — separate spotlights for work and personal. mark it done with a click.
- **two zones.** work and personal, one toggle (or ⌘1 / ⌘2). everything else lives inside a zone.
- **capture-first.** input is autofocused on load. enter saves. no required fields. no category picker.
- **mess-tolerant items.** paste a sketch right into capture and it becomes an item with a thumbnail. add notes inline. or just keep one-liners.
- **promote anything to spotlight.** hover an item, click the ↑.
- **clear-all-done with undo.** the done section has a counter; clearing is one click, undo lives for 5 seconds.
- **export to JSON** whenever — for backup or just to read your data outside the app.
- **light + dark.** sun/moon toggle in the header, honors `prefers-color-scheme` on first visit.
- **paper feel.** warm off-white, dashed rule, serif title, subtle dotted texture, ripped legal-pad accent on the right. not a saas dashboard.

## keyboard

- `enter` — save the current capture
- `⌘1` / `⌘2` — switch zones
- `/` — focus the capture field from anywhere
- paste an image directly into the capture field — it becomes an item with a thumbnail

## editing

everything is in `index.html` — one file, vanilla js, no framework, no build. open it locally in any browser, or edit on github and the live version updates within a minute (github pages auto-deploys from `main`).

things worth playing with if you want to tweak it:

- color palette: the css `:root` block at the top (`--paper`, `--ink`, `--spotlight-bg`, etc.); dark-mode overrides live in `html[data-theme="dark"]`
- the seed/sample items: the `seed` object in the script
- the zone labels ("work" / "personal"): in the html header
- the spotlight copy: the placeholder in `#spotlight-input`
- font: the `h1` rule (currently iowan old style with georgia fallback)
- the legal-pad SVG accent: at the top of `<body>`, can be removed entirely if you don't want it

## data + migrations

storage lives in `localStorage` under `jot.v2` — shape:

```js
{
  zone: 'work' | 'personal',
  spotlight: {
    work: { text, done, ts } | null,
    personal: { text, done, ts } | null
  },
  items: {
    work: [{ id, text, notes, img, done, ts }, ...],
    personal: [...]
  }
}
```

if you used the original jot (`jot.v1`), the app auto-migrates your items on first load and writes them into `jot.v2`. nothing is lost. the v1 data stays in localStorage as a backup.

## known limitations

- data lives only in this browser. no sync between devices, no backup beyond the export button.
- no real drawing surface — only image attachment.
- no due dates, reminders, recurring tasks, sub-tasks.
- accessibility still needs a pass (contrast, touch target sizes, screen-reader labels on the spotlight).

built as a starting point, not a finished product. open an issue or just edit it.

## credits

original jot — eferrao. spotlight + paper-pad aesthetic + dark-mode patterns — adapted from jocelynbaun/the-board. merged into a single vanilla-html app here.
