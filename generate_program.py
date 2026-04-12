#!/usr/bin/env python3
"""
generate_program.py — Build index.html from program_data.yml.

Run locally:  python generate_program.py
Called by:    .github/workflows/build.yml on every push that changes program_data.yml
"""

import re
import yaml
from pathlib import Path

# ── Slug helper (mirrors hymn_url.py) ────────────────────────────────────────
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
    return (
        f'<a class="hymn-link" href="{url}" target="_blank">'
        f'#{number} {title}</a>'
    )

# ── HTML helpers ─────────────────────────────────────────────────────────────
def esc(s: str) -> str:
    """Minimal HTML escaping."""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))

def render_program_row(item: dict) -> str:
    role = esc(item.get("role", ""))
    if "hymn_number" in item:
        right = hymn_link(item["hymn_number"], item["hymn_title"])
    else:
        right = esc(item.get("person", ""))
    return f"          <tr>\n            <td>{role}</td>\n            <td>{right}</td>\n          </tr>"

def render_cleaning(bc: dict) -> str:
    if not bc:
        return ""
    leader = esc(bc.get("leader", ""))
    families = bc.get("families", [])
    date_str = esc(bc.get("date", ""))

    pairs = ""
    for f in families:
        pairs += f"          <span>{esc(f)}</span>\n"

    return f"""      <div class="announcement">
        <h3>Building Cleaning Assignment</h3>
        <div class="ann-date">{date_str}</div>
        <div class="cleaning-leader">{leader}</div>
        <div class="cleaning-grid">
{pairs.rstrip()}
        </div>
        <p style="margin-top:.5rem;font-size:.8rem;text-align:center;">Cleaning time TBD by team leader</p>
      </div>"""

def render_events(events: list) -> str:
    if not events:
        return ""
    parts = []
    for ev in events:
        img = esc(ev.get("image", ""))
        alt = esc(ev.get("alt", ""))
        parts.append(
            f'      <div class="announcement">\n'
            f'        <img class="flyer" src="{img}" alt="{alt}" />\n'
            f'      </div>'
        )
    return "\n".join(parts)

# ── Main builder ─────────────────────────────────────────────────────────────
def build(data: dict) -> str:
    date      = esc(data.get("date", ""))
    time_str  = esc(data.get("time", ""))
    officers  = data.get("officers", {})

    presiding  = esc(officers.get("presiding", ""))
    conducting = esc(officers.get("conducting", ""))
    chorister  = esc(officers.get("chorister", ""))
    pianist    = esc(officers.get("pianist", ""))

    program_rows = "\n".join(render_program_row(item) for item in data.get("program", []))

    # Announcements
    bc      = data.get("building_cleaning", {})
    events  = data.get("events", [])

    cleaning_html = render_cleaning(bc)
    events_html   = render_events(events)

    # Build announcements body
    ann_parts = []
    if cleaning_html:
        ann_parts.append(cleaning_html)
    if events_html:
        if ann_parts:
            ann_parts.append('      <hr style="border:none;border-top:1px solid var(--rule);margin:.8rem 0;" />')
        ann_parts.append(events_html)
    announcements_body = "\n".join(ann_parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Sacrament Meeting – Clarkston Ward</title>
  <style>
    :root {{
      --navy: #1a2e4a;
      --gold:  #c9a84c;
      --light: #f7f5f0;
      --white: #ffffff;
      --text:  #222222;
      --muted: #666666;
      --rule:  #d0c9bc;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Georgia', 'Times New Roman', serif;
      background: var(--light);
      color: var(--text);
      line-height: 1.55;
    }}

    /* ── HEADER ── */
    header {{
      background: var(--navy);
      color: var(--white);
      padding: 1.6rem 1rem 1.2rem;
      text-align: center;
    }}
    header img.logo {{
      width: 72px;
      filter: brightness(0) invert(1);
      margin-bottom: .6rem;
    }}
    header h1 {{ font-size: 1.6rem; font-weight: normal; letter-spacing: .04em; }}
    header .date {{ font-size: 1.05rem; color: var(--gold); margin-top: .25rem; }}
    header .ward {{ font-size: .85rem; opacity: .8; margin-top: .4rem; letter-spacing: .05em; }}
    header .time {{ font-size: .9rem; color: var(--gold); margin-top: .2rem; }}

    /* ── MAIN CARD ── */
    main {{
      max-width: 680px;
      margin: 1.6rem auto;
      padding: 0 1rem 3rem;
    }}

    /* ── SECTION BLOCKS ── */
    .section {{
      background: var(--white);
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
      margin-bottom: 1.2rem;
      overflow: hidden;
    }}
    .section-header {{
      background: var(--navy);
      color: var(--white);
      font-size: .7rem;
      letter-spacing: .14em;
      text-transform: uppercase;
      padding: .45rem 1rem;
    }}
    .section-body {{ padding: .8rem 1rem; }}

    /* ── OFFICER GRID ── */
    .officers {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: .2rem .8rem;
      font-size: .88rem;
    }}
    .officer-item {{ display: flex; gap: .3rem; align-items: baseline; }}
    .officer-label {{ font-weight: bold; white-space: nowrap; color: var(--navy); }}
    .officer-name  {{ color: var(--muted); }}

    /* ── PROGRAM TABLE ── */
    .program-table {{ width: 100%; border-collapse: collapse; font-size: .92rem; }}
    .program-table tr {{ border-bottom: 1px solid var(--rule); }}
    .program-table tr:last-child {{ border-bottom: none; }}
    .program-table td {{ padding: .55rem .2rem; vertical-align: top; }}
    .program-table td:first-child {{
      font-weight: bold;
      color: var(--navy);
      width: 52%;
      padding-right: .8rem;
    }}
    .program-table td:last-child {{ color: var(--muted); }}
    .hymn-link {{
      color: var(--navy);
      text-decoration: none;
      border-bottom: 1px dotted var(--gold);
    }}
    .hymn-link:hover {{ border-bottom-style: solid; }}

    /* ── ANNOUNCEMENTS ── */
    .announcement {{ margin-bottom: 1rem; }}
    .announcement:last-child {{ margin-bottom: 0; }}
    .announcement h3 {{
      font-size: .95rem;
      color: var(--navy);
      margin-bottom: .2rem;
    }}
    .announcement .ann-date {{
      font-size: .82rem;
      color: var(--gold);
      font-style: italic;
      margin-bottom: .2rem;
    }}
    .announcement p {{ font-size: .88rem; color: var(--muted); }}
    .announcement img.flyer {{
      display: block;
      width: 100%;
      max-width: 480px;
      margin: .6rem auto 0;
      border-radius: 4px;
      box-shadow: 0 1px 6px rgba(0,0,0,.12);
    }}

    /* ── CLEANING TABLE ── */
    .cleaning-leader {{
      text-align: center;
      font-weight: bold;
      color: var(--navy);
      font-size: 1rem;
      padding: .4rem 0 .5rem;
    }}
    .cleaning-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: .1rem .8rem;
      font-size: .88rem;
      color: var(--muted);
      text-align: center;
    }}
    .cleaning-grid span {{ padding: .15rem 0; }}

    /* ── LINKS SECTION ── */
    .links-list {{ list-style: none; font-size: .88rem; }}
    .links-list li {{ padding: .35rem 0; border-bottom: 1px solid var(--rule); }}
    .links-list li:last-child {{ border-bottom: none; }}
    .links-list a {{ color: var(--navy); text-decoration: none; }}
    .links-list a:hover {{ text-decoration: underline; }}
    .links-list .link-label {{ font-weight: bold; color: var(--text); }}

    /* ── PDF DOWNLOAD ── */
    .pdf-btn {{
      display: block;
      text-align: center;
      background: var(--navy);
      color: var(--white);
      padding: .75rem 1rem;
      border-radius: 6px;
      font-size: .9rem;
      text-decoration: none;
      margin-top: .5rem;
      letter-spacing: .03em;
    }}
    .pdf-btn:hover {{ background: #243d60; }}

    /* ── FOOTER ── */
    footer {{
      text-align: center;
      font-size: .75rem;
      color: var(--muted);
      padding: 1.5rem 1rem;
    }}

    /* ── RESPONSIVE ── */
    @media (max-width: 480px) {{
      .officers {{ grid-template-columns: 1fr; }}
      header h1 {{ font-size: 1.35rem; }}
    }}
  </style>
</head>
<body>

<header>
  <img class="logo" src="images/word_media_image1.png" alt="The Church of Jesus Christ of Latter-day Saints" />
  <h1>Sacrament Meeting</h1>
  <div class="date">{date}</div>
  <div class="ward">Clarkston Ward &bull; Farmington Hills Michigan Stake</div>
  <div class="time">{time_str}</div>
</header>

<main>

  <!-- Officers -->
  <div class="section">
    <div class="section-body">
      <div class="officers">
        <div class="officer-item">
          <span class="officer-label">Presiding:</span>
          <span class="officer-name">{presiding}</span>
        </div>
        <div class="officer-item">
          <span class="officer-label">Chorister:</span>
          <span class="officer-name">{chorister}</span>
        </div>
        <div class="officer-item">
          <span class="officer-label">Conducting:</span>
          <span class="officer-name">{conducting}</span>
        </div>
        <div class="officer-item">
          <span class="officer-label">Pianist:</span>
          <span class="officer-name">{pianist}</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Program -->
  <div class="section">
    <div class="section-body">
      <table class="program-table">
        <tbody>
{program_rows}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Announcements -->
  <div class="section">
    <div class="section-header">Announcements</div>
    <div class="section-body">
{announcements_body}
    </div>
  </div>

  <!-- PDF Download -->
  <div class="section">
    <div class="section-body">
      <a class="pdf-btn" href="program.pdf" target="_blank">
        &#x1F4C4; Download / Print Full Program (PDF)
      </a>
    </div>
  </div>

  <!-- Links -->
  <div class="section">
    <div class="section-header">Ward Links</div>
    <div class="section-body">
      <ul class="links-list">
        <li>
          <span class="link-label">Clarkston Ward Website</span><br />
          <a href="https://local.churchofjesuschrist.org/en/units/us/mi/clarkston-ward">local.churchofjesuschrist.org</a>
        </li>
        <li>
          <span class="link-label">Ward History</span><br />
          <a href="https://unithistory.churchofjesuschrist.org/">unithistory.churchofjesuschrist.org</a>
        </li>
        <li>
          <span class="link-label">Clarkston Ward Facebook</span><br />
          <a href="http://tiny.cc/clarkstonfb">tiny.cc/clarkstonfb</a>
        </li>
        <li>
          <span class="link-label">Farmington Hills Stake Facebook</span><br />
          <a href="http://tiny.cc/farmingtonhillsfb">tiny.cc/farmingtonhillsfb</a>
        </li>
        <li>
          <span class="link-label">Stake Youth Instagram</span><br />
          @fhstakeyouth
        </li>
        <li>
          <span class="link-label">Emergency Action Plan</span><br />
          <a href="https://docs.google.com/document/d/1j_DFRv2XKlnHsu-Hh0mNoQG2S_QdeqUgVxPTIgz0oCw/edit?usp=sharing">View Document</a>
        </li>
        <li>
          <span class="link-label">Senior Missionary Opportunities</span><br />
          <a href="https://seniormissionary.churchofjesuschrist.org/srsite/cs/search?lang=eng">Senior Missionary Site</a>
        </li>
      </ul>
    </div>
  </div>

</main>

<footer>
  Clarkston Ward &bull; Farmington Hills Michigan Stake &bull; The Church of Jesus Christ of Latter-day Saints
</footer>

</body>
</html>
"""


if __name__ == "__main__":
    data_path = Path(__file__).parent / "program_data.yml"
    out_path  = Path(__file__).parent / "index.html"

    with open(data_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    html = build(data)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ Wrote {out_path} ({len(html):,} bytes)")
