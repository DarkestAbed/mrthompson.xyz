import re
from pathlib import Path
from fasthtml.common import *
import frontmatter
import mistune

from config import SITE_NAME, NAV_LINKS, UI_STRINGS

# ── Markdown engine ──────────────────────────────────────────────────────────
md = mistune.create_markdown(plugins=["table", "strikethrough", "task_lists"])


# ── Helpers ──────────────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text)


# ── Post loader ──────────────────────────────────────────────────────────────
def load_posts(lang: str = "en") -> list[dict]:
    base = Path("posts") / lang
    if not base.exists():
        return []
    posts = []
    seen_slugs: dict[str, str] = {}
    for path in base.glob("*.md"):
        post = frontmatter.load(path)
        if not post.get("published", False):
            continue
        slug = post.get("slug") or slugify(post.get("title", "")) or path.stem
        if slug in seen_slugs:
            raise ValueError(
                f"Slug collision: '{slug}' from '{path}' conflicts with '{seen_slugs[slug]}'"
            )
        seen_slugs[slug] = str(path)
        raw_date = post.get("date")
        posts.append(
            {
                "slug": slug,
                "title": post.get("title", slug),
                "date": raw_date,
                "date_str": raw_date.strftime("%B %d, %Y") if hasattr(raw_date, "strftime") else str(raw_date),
                "author": post.get("author", ""),
                "description": post.get("description", ""),
                "tags": post.get("tags", []),
                "content_html": md(post.content),
                "lang": lang,
            }
        )
    return sorted(posts, key=lambda p: p["date"], reverse=True)


def load_page(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        return ""
    post = frontmatter.load(path)
    return md(post.content)


# Build indexes at startup
POST_INDEX: dict[str, dict[str, dict]] = {
    "en": {p["slug"]: p for p in load_posts("en")},
    "es": {p["slug"]: p for p in load_posts("es")},
}


def get_post(slug: str, lang: str = "en") -> dict | None:
    return POST_INDEX[lang].get(slug)


def get_all_posts(lang: str = "en") -> list[dict]:
    return sorted(POST_INDEX[lang].values(), key=lambda p: p["date"], reverse=True)


# ── App setup ────────────────────────────────────────────────────────────────

# Reads theme cookie before first paint — prevents flash of wrong theme
theme_init = Script("""
(function(){
  var m = document.cookie.match(/(?:^|;\\s*)theme=([^;]+)/);
  if (m) document.documentElement.setAttribute('data-theme', m[1]);
})();
""")

pico_css = Link(
    rel="stylesheet",
    href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css",
)
custom_css = Link(rel="stylesheet", href="/static/custom.css")

app = FastHTML(
    hdrs=(theme_init, pico_css, custom_css),
    htmlkw={"data-theme": "dark"},
)


# ── Components ───────────────────────────────────────────────────────────────
def _toggle_lang(path: str, current_lang: str) -> str:
    other_lang = "es" if current_lang == "en" else "en"
    if path == "/":
        return "/posts/en/"
    parts = path.split("/")  # e.g. ["", "posts", "es", "slug"]
    if len(parts) >= 3 and parts[2] == current_lang:
        parts[2] = other_lang
        return "/".join(parts)
    return "/posts/en/" if other_lang == "en" else "/"


def nav_bar(lang: str, current_path: str):
    s = UI_STRINGS[lang]
    nav_links = [
        Li(A(label, href=href)) for label, href in NAV_LINKS[lang]
    ]

    lang_link = A(s["switch_lang"], href=_toggle_lang(current_path, lang), cls="lang-link")

    theme_btn = Button(
        s["toggle_theme"],
        cls="btn-theme",
        hx_post="/set-theme",
        hx_swap="none",
        hx_vals="js:{current_theme: document.documentElement.getAttribute('data-theme')}",
        onclick=(
            "var h=document.documentElement,"
            "n=h.getAttribute('data-theme')==='dark'?'light':'dark';"
            "h.setAttribute('data-theme',n);"
        ),
    )

    return Nav(
        Div(
            A(SITE_NAME, href="/", cls="nav-brand"),
            Ul(*nav_links, cls="nav-links"),
            Div(lang_link, theme_btn, cls="nav-controls"),
            cls="nav-inner container",
        ),
        cls="site-nav",
    )


def site_footer():
    return Footer(
        P("⚙ ", SITE_NAME, " — Transmissions from the Workshop ⚙"),
        cls="site-footer container",
    )


def page_shell(title: str, lang: str, current_path: str, *content):
    return (
        Title(f"{title} | {SITE_NAME}"),
        nav_bar(lang, current_path),
        Main(*content, cls="container"),
        site_footer(),
    )


def pipe_divider(label: str = "◈"):
    return Div(label, cls="pipe-divider")


def post_card(post: dict, lang: str):
    s = UI_STRINGS[lang]
    href = f"/posts/{lang}/{post['slug']}"
    tags = [Span(t, cls="tag") for t in post.get("tags", [])]
    return Article(
        H2(A(post["title"], href=href)),
        P(
            Span(s["posted_on"], " "),
            Span(post["date_str"], cls=""),
            (Span(f" {s['by']} " + post["author"]) if post.get("author") else ""),
            cls="post-meta",
        ),
        P(post["description"], cls="post-description") if post.get("description") else "",
        Div(*tags, cls="post-tags") if tags else "",
        A(s["read_more"], href=href, cls="read-more"),
        cls="post-card",
    )


def post_page_content(post: dict, lang: str):
    s = UI_STRINGS[lang]
    back_href = "/" if lang == "es" else "/posts/en/"
    tags = [Span(t, cls="tag") for t in post.get("tags", [])]
    return (
        Header(
            H1(post["title"]),
            P(
                Span(s["posted_on"], " "),
                Span(post["date_str"]),
                (Span(f" {s['by']} " + post["author"]) if post.get("author") else ""),
                cls="post-meta",
            ),
            Div(*tags, cls="post-tags") if tags else "",
            cls="post-header",
        ),
        Div(NotStr(post["content_html"]), cls="post-body"),
        Div(
            A(s["back_to_blog"], href=back_href, cls="back-link"),
            cls="post-footer",
        ),
    )


def not_found_page(lang: str):
    s = UI_STRINGS[lang]
    back_href = "/" if lang == "es" else "/posts/en/"
    return Div(
        H1("404"),
        P(s["not_found"]),
        P(s["not_found_detail"], cls="post-meta"),
        A(s["back_to_blog"], href=back_href, cls="back-link"),
        cls="not-found",
    )


# ── Routes — Spanish (default) ───────────────────────────────────────────────
@app.get("/")
@app.get("/posts/es/")
def blog_index_es(req):
    posts = get_all_posts("es")
    cards = [post_card(p, "es") for p in posts]
    content = (
        Div(
            H1("Transmisiones Tallerescas"),
            P("Despachos desde el taller etéreo.", cls="page-subtitle"),
            cls="page-header",
        ),
        pipe_divider(),
        Div(*cards, cls="post-list") if cards else P("Sin transmisiones aún.", cls="post-meta"),
    )
    return page_shell("Blog", "es", "/", *content)


@app.get("/posts/es/{slug}")
def blog_post_es(req, slug: str):
    post = get_post(slug, "es")
    if not post:
        return page_shell("No encontrado", "es", f"/posts/es/{slug}", not_found_page("es"))
    return page_shell(post["title"], "es", f"/posts/es/{slug}", *post_page_content(post, "es"))


@app.get("/pages/es/about")
def about_es(req):
    html = load_page("pages/es/about.md")
    return page_shell(
        "Sobre mí",
        "es",
        "/pages/es/about",
        Div(NotStr(html), cls="about-body"),
    )


# ── Routes — English ─────────────────────────────────────────────────────────
@app.get("/posts/en/")
def blog_index_en(req):
    posts = get_all_posts("en")
    cards = [post_card(p, "en") for p in posts]
    content = (
        Div(
            H1("The Workshop Transmissions"),
            P("Dispatches from the aetheric workshop.", cls="page-subtitle"),
            cls="page-header",
        ),
        pipe_divider(),
        Div(*cards, cls="post-list") if cards else P("No transmissions yet.", cls="post-meta"),
    )
    return page_shell("Blog", "en", "/posts/en/", *content)


@app.get("/posts/en/{slug}")
def blog_post_en(req, slug: str):
    post = get_post(slug, "en")
    if not post:
        return page_shell("Not Found", "en", f"/posts/en/{slug}", not_found_page("en"))
    return page_shell(post["title"], "en", f"/posts/en/{slug}", *post_page_content(post, "en"))


@app.get("/pages/en/about")
def about_en(req):
    html = load_page("pages/en/about.md")
    return page_shell(
        "About",
        "en",
        "/pages/en/about",
        Div(NotStr(html), cls="about-body"),
    )


# ── Theme toggle ─────────────────────────────────────────────────────────────
@app.post("/set-theme")
async def set_theme(req):
    form = await req.form()
    current = form.get("current_theme", "dark")
    new_theme = "light" if current == "dark" else "dark"
    resp = Response(status_code=204)
    resp.set_cookie("theme", new_theme, max_age=60 * 60 * 24 * 365, samesite="lax", path="/")
    return resp


# ── Static files ─────────────────────────────────────────────────────────────
@app.get("/static/{fname:path}")
async def static_files(fname: str):
    return FileResponse(f"static/{fname}")


# ── Entry point ───────────────────────────────────────────────────────────────
serve(port=5002)
