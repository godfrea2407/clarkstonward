"""
hymn_url.py — Generate churchofjesuschrist.org links for hymns.

Usage:
  python hymn_url.py "Precious Savior, Dear Redeemer"
  => https://www.churchofjesuschrist.org/media/music/songs/precious-savior-dear-redeemer?lang=eng

The slug rule: lowercase, drop apostrophes & commas & periods, replace spaces with hyphens.
"""

import re, sys

BASE = "https://www.churchofjesuschrist.org/media/music/songs/{slug}?lang=eng"

def hymn_url(title: str) -> str:
    """Convert a hymn title to its churchofjesuschrist.org URL."""
    slug = title.lower()
    slug = re.sub(r"[',\.\u2018\u2019\u201c\u201d]", "", slug)  # drop apostrophes/quotes/commas
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)                    # drop other punctuation
    slug = re.sub(r"\s+", "-", slug.strip())                     # spaces → hyphens
    slug = re.sub(r"-+", "-", slug)                              # collapse multiple hyphens
    return BASE.format(slug=slug)

def hymn_link(number: str, title: str) -> str:
    """Return an HTML anchor tag for a hymn."""
    url = hymn_url(title)
    return f'<a class="hymn-link" href="{url}" target="_blank">#{number} {title}</a>'

if __name__ == "__main__":
    for title in sys.argv[1:]:
        print(hymn_url(title))
