import markdown as md
import bleach

# Tags HTML autorisés après conversion Markdown
ALLOWED_TAGS = [
    "p", "br", "hr",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "em", "blockquote",
    "ul", "ol", "li",
    "code", "pre",
    "a",
    "table", "thead", "tbody", "tr", "th", "td",
]

# Attributs autorisés
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel", "target"],
    "code": ["class"],   # pour les classes pygments (language-*)
    "pre": ["class"],
    "th": ["align"],
    "td": ["align"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def render_markdown(text: str) -> str:
    """
    Convertit du Markdown en HTML, puis sanitize le HTML pour éviter toute injection.
    """
    text = text or ""

    html = md.markdown(
        text,
        extensions=[
            "fenced_code",   # ```code```
            "tables",        # tableaux
            "nl2br",         # retours à la ligne simples -> <br>
            "codehilite",    # coloration pygments (avec CSS à ajouter)
        ],
        extension_configs={
            "codehilite": {
                "guess_lang": False,
                "noclasses": False,  # on veut des classes CSS (meilleur)
            }
        },
        output_format="html5",
    )

    clean = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )

    # Transforme les URLs "nu" en liens (après clean)
    clean = bleach.linkify(
        clean,
        callbacks=[bleach.callbacks.nofollow, bleach.callbacks.target_blank],
        skip_tags=["pre", "code"],
        parse_email=True,
    )

    return clean