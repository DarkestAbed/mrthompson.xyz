# mrthompson.xyz — Blog Requirements & Developer Guide

## Stack

| Layer | Tool |
|---|---|
| Framework | FastHTML (Python) |
| Styling | PicoCSS v2 + custom steampunk overrides |
| Markdown parsing | Mistune 3.x |
| Frontmatter parsing | python-frontmatter |
| Package manager | uv |
| Server | Uvicorn (via FastHTML `serve()`) |

---

## Running the Blog

```bash
# Start the server
uv run python3 main.py

# Server runs at http://localhost:5002 with live reload enabled
```

---

## Project Structure

```
mrthompson.xyz/
├── main.py              # App entry point — routes, components, post loader
├── config.py            # Site constants, i18n strings, nav links
├── posts/               # English blog posts (Markdown)
│   └── es/              # Spanish blog post translations
├── pages/               # Static pages (About, etc.)
│   └── es/              # Spanish page translations
├── static/
│   └── custom.css       # Steampunk theme — all visual overrides on PicoCSS
├── pyproject.toml       # uv project config
└── REQUIREMENTS.md      # This file
```

---

## Functionalities

### Blog Post List (`/` and `/es/`)
- Reads all `.md` files from `posts/` (English) or `posts/es/` (Spanish)
- Only posts with `published: true` in frontmatter appear
- Posts are sorted by date, newest first
- Each card shows: title, transmission date, author, description excerpt, tags, and a "Read more" link

### Individual Post Pages (`/post/{slug}` and `/es/post/{slug}`)
- Route is determined by the `slug` field in frontmatter (or derived from the filename if absent)
- Renders full Markdown content as HTML, including tables, strikethrough, and task lists
- Displays title, date, author, and tags in a styled header
- "Back to workshop" link returns to the post list

### About Page (`/about` and `/es/about`)
- Reads from `pages/about.md` (English) or `pages/es/about.md` (Spanish)
- Falls back to the English version if no Spanish translation exists
- Plain Markdown content, no frontmatter required (though it can have a `title` field)

### Dark / Light Mode
- **Default:** dark mode (set server-side on the `<html>` tag)
- **Toggle:** the `☀ / ☾` button in the nav bar switches instantly via `onclick` (no page reload)
- **Persistence:** theme is stored in a 1-year cookie; an inline `<script>` in `<head>` reads it before first paint to prevent flash
- **Light mode aesthetic:** aged parchment background with dark ink — still steampunk

### Bilingual Support (English / Spanish)
- English is the default — no URL prefix (`/`, `/post/slug`, `/about`)
- Spanish uses the `/es/` prefix — `/es/`, `/es/post/slug`, `/es/about`
- The language toggle link in the nav bar mirrors the current page in the other language
- Each language has its own independent post index — a post only appears in Spanish if a matching `.md` file exists in `posts/es/`

---

## Adding a Blog Post

1. Create a new `.md` file in `posts/` (English) and optionally `posts/es/` (Spanish)
2. Add frontmatter at the top:

```yaml
---
title: Your Post Title
date: 2026-04-01
author: Mr. Thompson
published: true
slug: your-post-slug        # optional — derived from title if omitted
description: A short excerpt shown on the blog index card.
tags:
  - tag-one
  - tag-two
---

Your markdown content here...
```

3. Restart the server — the post index is built at startup

> **Note:** slugs must be unique per language. The server raises a `ValueError` on startup if two posts share the same slug.

### Frontmatter Fields

| Field | Required | Description |
|---|---|---|
| `title` | Yes | Post title, shown in the card and page header |
| `date` | Yes | Publication date (`YYYY-MM-DD`) — used for sorting |
| `author` | No | Shown in post meta |
| `published` | Yes | Set to `true` to make the post visible |
| `slug` | No | URL segment — derived from `title` if absent |
| `description` | No | Excerpt shown on the blog index card |
| `tags` | No | List of tag strings shown as labels |

---

## Editing the About Page

Edit `pages/about.md` (English) or `pages/es/about.md` (Spanish) directly. No frontmatter is required — pure Markdown works fine. Changes take effect on next server restart.

---

## Changing the Theme / Styles

All visual customisation lives in `static/custom.css`. The file is structured in sections:

- **CSS Custom Properties** — all colors and tokens for dark and light mode at the top; change palette here
- **Typography** — Google Fonts (`Playfair Display`, `Jost`, `Share Tech Mono`)
- **Navigation** — `.site-nav`, `.nav-brand`, `.nav-links`, `.nav-controls`
- **Post Cards** — `.post-card`, `.post-meta`, `.post-tags`
- **Individual Post** — `.post-header`, `.post-body`, `.post-footer`
- **About Page** — `.about-body`
- **Pipe Divider / Rivet decorations** — `.pipe-divider`, `.riveted`

PicoCSS is loaded from CDN and handles layout, spacing, and accessibility defaults. The custom CSS overrides its design tokens via `--pico-*` variables and adds the steampunk layer on top.

---

## Adding a New Page

1. Create a Markdown file in `pages/` (and `pages/es/` for Spanish)
2. Add a route in `main.py`:

```python
@app.get("/new-page")
def new_page(req):
    html = load_page("pages/new-page.md")
    return page_shell("New Page", "en", "/new-page", Div(NotStr(html), cls="about-body"))
```

3. Add the nav link in `config.py` under `NAV_LINKS`:

```python
NAV_LINKS = {
    "en": [("Blog", "/"), ("About", "/about"), ("New Page", "/new-page")],
    "es": [..., ("Nueva Página", "/es/new-page")],
}
```

---

## Adding UI Strings (i18n)

All user-facing strings live in `config.py` under `UI_STRINGS`. To add a new string:

```python
UI_STRINGS = {
    "en": { ..., "my_new_string": "Hello" },
    "es": { ..., "my_new_string": "Hola" },
}
```

Then access it in `main.py` via `UI_STRINGS[lang]["my_new_string"]`.
