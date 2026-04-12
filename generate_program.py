#!/usr/bin/env python3
"""
generate_program.py — Build index.html (and optionally program.pdf) from program_data.yml.

Usage:
  python generate_program.py          # generates index.html only
  python generate_program.py --pdf    # generates index.html + program.pdf via WeasyPrint
"""

import re
import sys
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ── Slug / hymn-link helpers ──────────────────────────────────────────────────
BASE_HYMN_URL = "https://www.churchofjesuschrist.org/media/music/songs/{slug}?lang=eng"

def hymn_url(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[',\.\u2018\u2019\u201c\u201d]", "", slug)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return BASE_HYMN_URL.format(slug=slug)

def hymn_link(number, title: str) -> str:
    url = hymn_url(title)
    return f'<a class="hymn-link" href="{url}" target="_blank">#{number} {title}</a>'

def esc(s: str) -> str:
    return (str(s)
            .replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))

# ── Section renderers ─────────────────────────────────────────────────────────
def render_program_row(item: dict) -> str:
    role = esc(item.get("role", ""))
    if "hymn_number" in item:
        right = hymn_link(item["hymn_number"], item["hymn_title"])
    else:
        right = esc(item.get("person", ""))
    return f'          <tr><td>{role}</td><td>{right}</td></tr>'

def render_cleaning(bc: dict) -> str:
    if not bc:
        return ""
    leader   = esc(bc.get("leader", ""))
    date_str = esc(bc.get("date", ""))
    families = bc.get("families", [])
    pairs    = "".join(f"<span>{esc(f)}</span>" for f in families)
    return f"""      <div class="ann-block">
        <div class="ann-title">Building Cleaning &mdash; <span class="ann-date">{date_str}</span></div>
        <div class="cleaning-leader">{leader}</div>
        <div class="cleaning-grid">{pairs}</div>
      </div>"""

def render_events(events: list) -> str:
    parts = []
    for ev in events:
        img = esc(ev.get("image", ""))
        alt = esc(ev.get("alt", ""))
        parts.append(f'      <div class="ann-block"><img class="flyer" src="{img}" alt="{alt}" /></div>')
    return "\n".join(parts)

# ── Main HTML builder ─────────────────────────────────────────────────────────
def build(data: dict) -> str:
    date     = esc(data.get("date", ""))
    time_str = esc(data.get("time", ""))
    o        = data.get("officers", {})

    presiding  = esc(o.get("presiding", ""))
    conducting = esc(o.get("conducting", ""))
    chorister  = esc(o.get("chorister", ""))
    pianist    = esc(o.get("pianist", ""))

    program_rows = "\n".join(render_program_row(i) for i in data.get("program", []))

    bc            = data.get("building_cleaning", {})
    events        = data.get("events", [])
    cleaning_html = render_cleaning(bc)
    events_html   = render_events(events)

    ann_parts = []
    if cleaning_html:
        ann_parts.append(cleaning_html)
    if events_html:
        ann_parts.append(events_html)
    ann_body = "\n      <hr class='ann-rule' />\n".join(ann_parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sacrament Meeting &ndash; Clarkston Ward</title>
  <style>
    /* ── Variables ── */
    :root {{
      --navy:  #1a2e4a;
      --gold:  #c9a84c;
      --light: #f7f4ee;
      --white: #ffffff;
      --text:  #1a1a1a;
      --muted: #555555;
      --rule:  #d4cec4;
    }}

    /* ── Reset & base ── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ font-size: 13px; }}
    body {{
      font-family: 'Georgia', 'Times New Roman', serif;
      background: var(--light);
      color: var(--text);
      line-height: 1.4;
    }}

    /* ── Page wrapper — single-column, max 680px ── */
    .page {{
      max-width: 680px;
      margin: 0 auto;
      background: var(--white);
      box-shadow: 0 2px 12px rgba(0,0,0,.10);
    }}

    /* ── Header ── */
    header {{
      background: var(--navy);
      color: var(--white);
      text-align: center;
      padding: .9rem 1rem .7rem;
    }}
    header img.logo {{
      width: 54px;
      filter: brightness(0) invert(1);
      margin-bottom: .35rem;
      display: block;
      margin-left: auto;
      margin-right: auto;
    }}
    header h1  {{ font-size: 1.25rem; font-weight: normal; letter-spacing: .04em; }}
    header .hdate {{ font-size: .95rem; color: var(--gold); margin-top: .15rem; }}
    header .hward {{ font-size: .72rem; opacity: .75; margin-top: .2rem; letter-spacing: .05em; }}
    header .htime {{ font-size: .8rem; color: var(--gold); margin-top: .1rem; }}

    /* ── Shared card styles ── */
    .card {{
      border-bottom: 1px solid var(--rule);
      padding: .55rem .9rem;
    }}
    .card-label {{
      font-size: .6rem;
      letter-spacing: .13em;
      text-transform: uppercase;
      color: var(--white);
      background: var(--navy);
      display: inline-block;
      padding: .15rem .5rem;
      margin-bottom: .35rem;
    }}

    /* ── Officers ── */
    .officers {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: .15rem .6rem;
      font-size: .8rem;
    }}
    .off-item  {{ display: flex; gap: .25rem; align-items: baseline; }}
    .off-label {{ font-weight: bold; color: var(--navy); white-space: nowrap; }}
    .off-name  {{ color: var(--muted); }}

    /* ── Program table ── */
    .prog-table {{ width: 100%; border-collapse: collapse; font-size: .82rem; }}
    .prog-table tr {{ border-bottom: 1px solid var(--rule); }}
    .prog-table tr:last-child {{ border-bottom: none; }}
    .prog-table td {{ padding: .32rem .15rem; vertical-align: top; }}
    .prog-table td:first-child {{
      font-weight: bold; color: var(--navy);
      width: 50%; padding-right: .6rem;
    }}
    .prog-table td:last-child {{ color: var(--muted); }}
    .hymn-link {{
      color: var(--navy); text-decoration: none;
      border-bottom: 1px dotted var(--gold);
    }}
    .hymn-link:hover {{ border-bottom-style: solid; }}

    /* ── Announcements ── */
    .ann-block {{ margin-bottom: .5rem; }}
    .ann-block:last-child {{ margin-bottom: 0; }}
    .ann-title {{ font-size: .8rem; font-weight: bold; color: var(--navy); margin-bottom: .15rem; }}
    .ann-date  {{ font-weight: normal; font-style: italic; color: var(--gold); }}
    .ann-rule  {{ border: none; border-top: 1px solid var(--rule); margin: .45rem 0; }}
    .cleaning-leader {{
      text-align: center; font-weight: bold; color: var(--navy);
      font-size: .85rem; padding: .2rem 0 .25rem;
    }}
    .cleaning-grid {{
      display: grid; grid-template-columns: 1fr 1fr;
      gap: .05rem .5rem; font-size: .78rem; color: var(--muted); text-align: center;
    }}
    .flyer {{
      display: block; width: 100%; max-width: 420px;
      margin: .35rem auto 0; border-radius: 3px;
      box-shadow: 0 1px 5px rgba(0,0,0,.12);
    }}

    /* ── PDF button ── */
    .pdf-btn {{
      display: block; text-align: center;
      background: var(--navy); color: var(--white);
      padding: .5rem .8rem; font-size: .82rem;
      text-decoration: none; letter-spacing: .03em;
    }}
    .pdf-btn:hover {{ background: #243d60; }}

    /* ── Links ── */
    .links-list {{ list-style: none; font-size: .78rem; }}
    .links-list li {{ padding: .28rem 0; border-bottom: 1px solid var(--rule); }}
    .links-list li:last-child {{ border-bottom: none; }}
    .links-list a {{ color: var(--navy); text-decoration: none; }}
    .links-list a:hover {{ text-decoration: underline; }}
    .link-label {{ font-weight: bold; color: var(--text); }}

    /* ── Footer ── */
    footer {{
      background: var(--navy); color: rgba(255,255,255,.6);
      text-align: center; font-size: .65rem;
      padding: .45rem .5rem; letter-spacing: .04em;
    }}

    /* ── Responsive ── */
    @media (max-width: 480px) {{
      html {{ font-size: 12px; }}
      .officers {{ grid-template-columns: 1fr; }}
    }}

    /* ── Print ── */
    @media print {{
      html {{ font-size: 11px; }}
      body {{ background: white; }}
      .page {{ box-shadow: none; max-width: 100%; }}
      .pdf-btn {{ display: none; }}
      a {{ color: inherit !important; border-bottom: none !important; }}
    }}
  </style>
</head>
<body>
<div class="page">

  <header>
    <img class="logo" src="images/word_media_image1.png" alt="The Church of Jesus Christ of Latter-day Saints" />
    <h1>Sacrament Meeting</h1>
    <div class="hdate">{date}</div>
    <div class="hward">Clarkston Ward &bull; Farmington Hills Michigan Stake</div>
    <div class="htime">{time_str}</div>
  </header>

  <!-- Officers -->
  <div class="card">
    <div class="officers">
      <div class="off-item"><span class="off-label">Presiding:</span><span class="off-name">{presiding}</span></div>
      <div class="off-item"><span class="off-label">Chorister:</span><span class="off-name">{chorister}</span></div>
      <div class="off-item"><span class="off-label">Conducting:</span><span class="off-name">{conducting}</span></div>
      <div class="off-item"><span class="off-label">Pianist:</span><span class="off-name">{pianist}</span></div>
    </div>
  </div>

  <!-- Program -->
  <div class="card">
    <table class="prog-table">
      <tbody>
{program_rows}
      </tbody>
    </table>
  </div>

  <!-- Announcements -->
  <div class="card">
    <div class="card-label">Announcements</div>
{ann_body}
  </div>

  <!-- PDF Download -->
  <a class="pdf-btn" href="program.pdf" target="_blank">&#x1F4C4;&nbsp; Download / Print Program (PDF)</a>

  <!-- Ward Links -->
  <div class="card">
    <div class="card-label">Ward Links</div>
    <ul class="links-list">
      <li><span class="link-label">Clarkston Ward Website</span><br /><a href="https://local.churchofjesuschrist.org/en/units/us/mi/clarkston-ward">local.churchofjesuschrist.org</a></li>
      <li><span class="link-label">Ward History</span><br /><a href="https://unithistory.churchofjesuschrist.org/">unithistory.churchofjesuschrist.org</a></li>
      <li><span class="link-label">Clarkston Ward Facebook</span><br /><a href="http://tiny.cc/clarkstonfb">tiny.cc/clarkstonfb</a></li>
      <li><span class="link-label">Farmington Hills Stake Facebook</span><br /><a href="http://tiny.cc/farmingtonhillsfb">tiny.cc/farmingtonhillsfb</a></li>
      <li><span class="link-label">Stake Youth Instagram</span><br />@fhstakeyouth</li>
      <li><span class="link-label">Emergency Action Plan</span><br /><a href="https://docs.google.com/document/d/1j_DFRv2XKlnHsu-Hh0mNoQG2S_QdeqUgVxPTIgz0oCw/edit?usp=sharing">View Document</a></li>
      <li><span class="link-label">Senior Missionary Opportunities</span><br /><a href="https://seniormissionary.churchofjesuschrist.org/srsite/cs/search?lang=eng">Senior Missionary Site</a></li>
    </ul>
  </div>

  <footer>Clarkston Ward &bull; Farmington Hills Michigan Stake &bull; The Church of Jesus Christ of Latter-day Saints</footer>

</div>
</body>
</html>
"""

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data_path = BASE_DIR / "program_data.yml"
    out_html  = BASE_DIR / "index.html"
    out_pdf   = BASE_DIR / "program.pdf"

    with open(data_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    html = build(data)

    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ Wrote {out_html}")

    if "--pdf" in sys.argv:
        import subprocess, os
        env = os.environ.copy()
        env["PATH"] = env.get("PATH", "") + ":/sessions/awesome-nifty-allen/.local/bin"
        result = subprocess.run(
            ["weasyprint", str(out_html), str(out_pdf)],
            capture_output=True, text=True, env=env
        )
        if result.returncode == 0:
            import os as _os
            size = _os.path.getsize(out_pdf)
            print(f"✓ Wrote {out_pdf} ({size//1024}KB)")
        else:
            print("WeasyPrint error:", result.stderr[:300])
