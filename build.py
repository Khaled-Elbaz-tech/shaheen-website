#!/usr/bin/env python3
"""Ola Magdy portfolio — static site generator.

Reads content.json + site.json (+ assets.json) and renders dist/:
  index.html, project-index/index.html, projects/<id>/index.html,
  style.css, site.js.

All paths emitted are relative (no root-absolute URLs). Python 3 stdlib only.
Idempotent: re-running produces byte-identical output.
"""
from pathlib import Path
import json, html, re, sys, shutil

ROOT = Path(__file__).parent
D = ROOT / 'dist'

C = json.loads((ROOT / 'content.json').read_text(encoding='utf-8'))
A = json.loads((ROOT / 'assets.json').read_text(encoding='utf-8'))
GROUPS = {g['id']: g for g in C['groups']}
# CMS publishing: drafts and archived projects never reach the public site.
ORDERED = sorted(
    (g for g in C['groups'] if g.get('status', 'published') not in ('draft', 'archived')),
    key=lambda g: g['number'])

e = html.escape

# Asset version for cache-busting. Bump this when CSS/JS changes.
ASSET_V = "9"

# ---------------------------------------------------------------- site.json
# Shared contract with the PHP CMS. Every value below is a default; anything
# present in site.json overrides it. The site builds cleanly without site.json.

DEFAULT_SITE = {
    "hero": {
        "headline": "Spaces that move us.",
        "descriptor": "ARCHITECTURE · LANDSCAPE · PLACE",
        "image": "d34s027i0",
        "project_id": "sohra-culture",
        "alt": "Sohra Culture & Experience Centre — design visualisation",
    },
    "intro": {
        "eyebrow": "The practice — a personal perspective",
        "statement": "Thinking across scales. Designing with place.",
        "copy": "",
    },
    "studio": {
        "headline": "A practice shaped by curiosity.",
        "intro": "",
        "bio": "",
        "philosophy": "",
        "image": "",
        "image_alt": "",
        "image_caption": "",
    },
    "approach": {
        "headline": "Thinking across scales. Designing with place.",
        "intro": "",
        "stages": [
            {"n": "01", "title": "Listen",
             "text": "Understand the people, place, context, and brief."},
            {"n": "02", "title": "Explore",
             "text": "Research the site, analyze constraints, and investigate possibilities."},
            {"n": "03", "title": "Shape",
             "text": "Translate insights into concepts, spatial strategies, and design proposals."},
            {"n": "04", "title": "Deliver",
             "text": "Refine the design and coordinate its development toward implementation."},
        ],
    },
    "landscape_gallery": {"headline": "In dialogue with the landscape.",
                          "intro": "", "images": []},
    "journal": [],
    "contact": {"headline": "Let's start a conversation.",
                "copy": "", "email": "", "socials": {}},
    "nav": [
        {"label": "Work", "href": "#work"},
        {"label": "Studio", "href": "#studio"},
        {"label": "Approach", "href": "#approach"},
        {"label": "Journal", "href": "#journal"},
        {"label": "Contact", "href": "#contact"},
    ],
    "sections_order": ["hero", "intro", "work", "landscape", "studio",
                       "approach", "journal", "contact"],
    "seo": {"title": "Ola Magdy — Architecture, Landscape & Urbanism",
            "description": "",
            "og_image": "d34s027i0"},
}


def deep_merge(base, override):
    """Recursive dict merge; override wins. Lists are replaced wholesale."""
    if isinstance(base, dict) and isinstance(override, dict):
        out = dict(base)
        for k, v in override.items():
            out[k] = deep_merge(out[k], v) if k in out else v
        return out
    return override


try:
    SITE = deep_merge(DEFAULT_SITE,
                      json.loads((ROOT / 'site.json').read_text(encoding='utf-8')))
    site_src = 'site.json'
except FileNotFoundError:
    SITE = DEFAULT_SITE
    site_src = 'defaults (site.json missing)'
except json.JSONDecodeError as ex:
    print(f'WARNING: site.json is invalid JSON ({ex}); using defaults.',
          file=sys.stderr)
    SITE = DEFAULT_SITE
    site_src = 'defaults (site.json invalid)'

DRAWING_RE = re.compile(
    r'masterplan|master plan|site plan|floor plan|section|elevation|'
    r'axonometr|model|sketch|drawing|diagram|layout', re.I)

warnings = []


def asset(key):
    a = A.get(key)
    if a is None:
        warnings.append(f'missing asset key: {key}')
    return a


def img(key, alt, eager=False, cls='', p=''):
    """Image with intrinsic dimensions (no layout shift)."""
    a = asset(key)
    if a is None:
        return ''
    cls_a = f' class="{cls}"' if cls else ''
    load = 'eager' if eager else 'lazy'
    fp = ' fetchpriority="high"' if eager else ''
    return (f'<img src="{p}assets/{key}.webp" width="{a["width"]}"'
            f' height="{a["height"]}" alt="{e(alt)}"{cls_a}'
            f' loading="{load}" decoding="async"{fp}>')


def arrow():
    return '<span class="arr" aria-hidden="true">↗</span>'


def journal_published():
    """Journal entries visible on the public site (published only)."""
    return [j for j in (SITE.get('journal') or [])
            if j.get('status', 'published') == 'published']


def nav_items(p):
    """Header nav from site.json, minus Journal when the journal is empty."""
    items = []
    for n in SITE.get('nav', []):
        if n.get('href') == '#journal' and not journal_published():
            continue
        items.append(
            f'<a class="nav-link" href="{p}{e(n["href"])}">'
            f'<span>{e(n["label"])}</span></a>')
    items.append(
        f'<a class="nav-link nav-index" href="{p}project-index/">'
        f'<span>Index</span>{arrow()}</a>')
    return '\n'.join(items)


def lightbox_markup():
    return '''<div class="lb" id="lightbox" role="dialog" aria-modal="true"
     aria-label="Image viewer" hidden>
  <div class="lb-backdrop" data-lb="close"></div>
  <figure class="lb-figure">
    <img class="lb-img" src="" alt="">
    <figcaption class="lb-cap"></figcaption>
  </figure>
  <p class="lb-count" aria-live="polite"></p>
  <button class="lb-btn lb-prev" data-lb="prev" aria-label="Previous image">←</button>
  <button class="lb-btn lb-next" data-lb="next" aria-label="Next image">→</button>
  <button class="lb-btn lb-close" data-lb="close" aria-label="Close viewer">×</button>
</div>'''


def shell(title, desc, body, p='', page='', og_image=None):
    """Full page shell. p = relative prefix to dist root ('', '../', '../../')."""
    seo = SITE.get('seo', {})
    og = og_image or seo.get('og_image') or ''
    og_tag = (f'\n<meta property="og:image" content="{p}assets/{og}.webp">'
              if og and asset(og) else '')
    email = SITE.get('contact', {}).get('email') or ''
    canonical = 'https://olamagdy.example/'  # placeholder — replace on launch
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc.strip()[:300])}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Ola Magdy — Architecture">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc.strip()[:300])}">{og_tag}
<meta name="theme-color" content="#171A17">
<link rel="icon" href="{p}favicon.svg" type="image/svg+xml">
<script>document.documentElement.classList.add('js');</script>
<link rel="stylesheet" href="{p}style.css?v={ASSET_V}">
<script src="{p}site.js?v={ASSET_V}" defer></script>
</head>
<body class="{page}">
<a class="skip" href="#main">Skip to content</a>
<div class="progress" aria-hidden="true"><span id="progressBar"></span></div>
<header class="site-header" id="siteHeader">
  <div class="head-inner">
    <a class="wordmark" href="{p}" aria-label="Ola Magdy — home">OLA&nbsp;MAGADY<span class="wm-dot">.</span></a>
    <nav class="site-nav" aria-label="Primary">
      {nav_items(p)}
    </nav>
    <div class="head-actions">
      <a class="btn btn-outline head-cta" href="#contact">Get in touch</a>
      <button class="menu-btn" id="menuBtn" aria-expanded="false"
              aria-controls="menuOverlay" aria-label="Open menu">
        <span></span><span></span>
      </button>
    </div>
  </div>
</header>
<div class="menu-overlay" id="menuOverlay" hidden>
  <nav aria-label="Menu">
    {nav_items(p)}
  </nav>
  <p class="menu-note">Ola Magdy — Architecture, Landscape &amp; Urbanism</p>
</div>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="foot-top">
      <a class="foot-word" href="{p}" aria-label="Ola Magdy — home">OLA&nbsp;MAGADY<span class="wm-dot">.</span></a>
      <div class="foot-cols">
        <div class="foot-col">
          <h4>Studio</h4>
          <a href="{p}#work">Work</a>
          <a href="{p}#services">Services</a>
          <a href="{p}#approach">Approach</a>
          <a href="{p}project-index/">Project Index</a>
        </div>
        <div class="foot-col">
          <h4>Contact</h4>
          <a href="mailto:{email}">{email}</a>
          <p>Architecture &middot; Landscape &middot; Place</p>
        </div>
        <div class="foot-col">
          <h4>Follow</h4>
          <a href="#" rel="noopener">Instagram</a>
          <a href="#" rel="noopener">LinkedIn</a>
          <a href="#" rel="noopener">Behance</a>
        </div>
      </div>
    </div>
    <div class="foot-base">
      <p>&copy; 2026 OLA MAGADY. All rights reserved.</p>
      <nav aria-label="Legal">
        <a href="#">Privacy Policy</a>
        <a href="#">Terms of Service</a>
      </nav>
    </div>
  </div>
</footer>
{lightbox_markup()}
</body>
</html>
'''

# ---------------------------------------------------------------- styles

CSS = '''/* OLA MAGADY — ARCOVA-inspired dark luxury system.
   Deep black / warm gold / cream. Instrument Serif display, Manrope text.
   All asset URLs relative. */

@font-face{
  font-family:"Instrument Serif";font-style:normal;font-weight:400;
  font-display:swap;src:url("fonts/instrument-regular.ttf") format("truetype");
}
@font-face{
  font-family:"Instrument Serif";font-style:italic;font-weight:400;
  font-display:swap;src:url("fonts/instrument-italic.ttf") format("truetype");
}
@font-face{
  font-family:"Manrope";font-style:normal;font-weight:400;
  font-display:swap;src:url("fonts/manrope-400.ttf") format("truetype");
}
@font-face{
  font-family:"Manrope";font-style:normal;font-weight:600;
  font-display:swap;src:url("fonts/manrope-600.ttf") format("truetype");
}
@font-face{
  font-family:"Manrope";font-style:normal;font-weight:700;
  font-display:swap;src:url("fonts/manrope-700.ttf") format("truetype");
}

:root{
  --black:#0A0A0A; --ink:#111111; --charcoal:#171A17; --card:#161616; --card-2:#1B1B1B;
  --gold:#C6A15B; --gold-lt:#D3B36C; --gold-deep:#9A7B40;
  --cream:#F8F6F1; --cream-2:#F1EDE4; --ivory:#F2F0E9; --white:#FAF9F5;
  --mut:rgba(250,249,245,.64); --mut-soft:rgba(250,249,245,.44);
  --mut-d:#6B6B6B; --ink-text:#1A1A1A;
  --line-d:rgba(250,249,245,.10); --line-d-soft:rgba(250,249,245,.07);
  --line-l:rgba(10,10,10,.10);
  --serif:"Instrument Serif",Georgia,"Times New Roman",serif;
  --sans:"Manrope",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --wrap:1440px;
  --pad:clamp(20px,4vw,60px);
  --ease:cubic-bezier(.22,.61,.21,1);
  --radius:14px;
}

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{
  font-family:var(--sans);font-weight:400;font-size:1.0625rem;line-height:1.7;
  color:var(--white);background:var(--black);
  -webkit-font-smoothing:antialiased;overflow-x:hidden;
}
img{max-width:100%;height:auto;display:block}
a{color:inherit}
::selection{background:var(--gold);color:var(--black)}

:focus{outline:none}
:focus-visible{outline:2px solid var(--gold);outline-offset:3px;border-radius:2px}

.skip{
  position:fixed;top:-60px;left:16px;z-index:200;background:var(--gold);
  color:var(--black);padding:.6rem 1.1rem;font-size:.85rem;text-decoration:none;
  border-radius:0 0 6px 6px;transition:top .2s var(--ease);font-weight:600;
}
.skip:focus{top:0}

.wrap{max-width:var(--wrap);margin-inline:auto;padding-inline:var(--pad)}
.sec{padding-block:clamp(4.5rem,8vw,8rem)}
.sec-light{background:var(--cream);color:var(--ink-text)}
.sec-dark{background:var(--black);color:var(--white)}

/* ---------- reveal animations ---------- */
.js [data-rv]{opacity:0;transform:translateY(28px);
  transition:opacity .9s var(--ease),transform .9s var(--ease)}
.js [data-rv].in{opacity:1;transform:none}
.js [data-rv="d1"]{transition-delay:.12s}
.js [data-rv="d2"]{transition-delay:.24s}
.js [data-rv="d3"]{transition-delay:.36s}

/* ---------- scroll progress ---------- */
.progress{position:fixed;top:0;left:0;right:0;height:2px;z-index:120;
  background:transparent;pointer-events:none}
.progress span{display:block;height:100%;width:100%;background:var(--gold);
  transform-origin:0 50%;transform:scaleX(0)}

/* ---------- header ---------- */
.site-header{
  position:fixed;top:0;left:0;right:0;z-index:100;
  transition:background .4s var(--ease),border-color .4s var(--ease),backdrop-filter .4s;
  border-bottom:1px solid transparent;
}
.site-header .head-inner{
  max-width:var(--wrap);margin-inline:auto;padding-inline:var(--pad);
  display:flex;align-items:center;justify-content:space-between;gap:1.25rem;
  height:76px;flex-wrap:nowrap;
}
.site-header.scrolled{
  background:rgba(23,26,23,.92);backdrop-filter:blur(18px) saturate(1.15);-webkit-backdrop-filter:blur(18px) saturate(1.15);
  border-bottom-color:var(--line-d-soft);
}
.wordmark{
  font-family:var(--serif);font-size:1.45rem;font-weight:700;letter-spacing:.1em;
  text-decoration:none;color:var(--white);white-space:nowrap;flex:none;
  text-shadow:0 1px 8px rgba(0,0,0,.5);
}
.wordmark .wm-dot{color:var(--gold)}
.head-actions{display:flex;align-items:center;gap:.9rem;flex:none}
.head-cta{
  padding:.72rem 1.35rem;font-size:.72rem;white-space:nowrap;
}
.site-nav{display:flex;align-items:center;gap:clamp(1.1rem,2.4vw,2.2rem);flex-wrap:nowrap;min-width:0}
.nav-link{
  font-size:.85rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;
  text-decoration:none;color:rgba(255,255,255,.8);position:relative;padding:.4rem 0;
  transition:color .3s var(--ease);text-shadow:0 1px 6px rgba(0,0,0,.5);
}
.nav-link::after{
  content:"";position:absolute;left:0;bottom:0;height:1px;width:100%;
  background:var(--gold);transform:scaleX(0);transform-origin:0 50%;
  transition:transform .35s var(--ease);
}
.nav-link:hover,.nav-link:focus-visible{color:var(--white)}
.nav-link:hover::after,.nav-link:focus-visible::after{transform:scaleX(1)}
.btn{
  display:inline-flex;align-items:center;gap:.7em;
  font-size:.78rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase;
  text-decoration:none;cursor:pointer;border:1px solid transparent;
  padding:1rem 1.9rem;border-radius:4px;
  transition:background .3s var(--ease),color .3s var(--ease),border-color .3s var(--ease),transform .3s var(--ease);
}
.btn-gold{background:var(--gold);color:var(--charcoal)}
.btn-gold:hover{background:var(--gold-lt);transform:translateY(-2px)}
.btn-gold:focus-visible{outline:2px solid var(--white);outline-offset:3px}
.btn-outline{border-color:rgba(201,169,97,.5);color:var(--gold);background:transparent}
.btn-outline:hover{border-color:var(--gold);background:rgba(201,169,97,.1)}
.btn-outline-d{border-color:rgba(10,10,10,.25);color:var(--ink-text)}
.btn-outline-d:hover{border-color:var(--ink-text);background:rgba(10,10,10,.05)}
.btn .arr{font-size:1.1em;line-height:1}
.menu-btn{
  display:none;background:none;border:0;cursor:pointer;padding:.6rem;
  flex-direction:column;gap:6px;
}
.menu-btn span{display:block;width:26px;height:2px;background:var(--white);transition:.3s var(--ease)}
.menu-overlay{
  position:fixed;inset:0;z-index:99;background:rgba(10,10,10,.97);
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1.2rem;
}
.menu-overlay[hidden]{display:none}
.menu-overlay .nav-link{font-size:1.4rem}
.menu-note{color:var(--mut-soft);font-size:.85rem;margin-top:1rem}

/* ---------- hero ---------- */
.hero{
  position:relative;min-height:100svh;min-height:100dvh;display:flex;align-items:center;
  overflow:hidden;background:var(--charcoal);
}
.hero-media{position:absolute;inset:0}
.hero-media img{
  width:100%;height:100%;object-fit:cover;object-position:62% 38%;
  animation:heroSettle 9s var(--ease) both;
}
@keyframes heroSettle{from{transform:scale(1.07)}to{transform:scale(1)}}
.hero-scrim{
  position:absolute;inset:0;pointer-events:none;
  background:
    linear-gradient(100deg,rgba(23,26,23,.86) 0%,rgba(23,26,23,.60) 32%,rgba(23,26,23,.12) 60%,rgba(23,26,23,.30) 100%),
    linear-gradient(0deg,rgba(23,26,23,.94) 0%,rgba(23,26,23,0) 46%);
}
.hero-inner{
  position:relative;z-index:2;width:100%;max-width:var(--wrap);
  margin-inline:auto;padding-inline:var(--pad);
  padding-top:clamp(6.5rem,15vh,9.5rem);padding-bottom:clamp(8.5rem,19vh,12rem);
}
.hero-over{
  font-size:.78rem;font-weight:700;letter-spacing:.26em;text-transform:uppercase;
  color:var(--gold-lt);margin-bottom:1.5rem;
  text-shadow:0 1px 8px rgba(0,0,0,.7);
}
.hero-title{
  font-family:var(--serif);font-weight:400;
  font-size:clamp(2.7rem,6vw,5.4rem);line-height:1.06;letter-spacing:-.01em;
  color:var(--white);max-width:13ch;margin-bottom:1.5rem;
  text-shadow:0 2px 24px rgba(0,0,0,.65),0 1px 6px rgba(0,0,0,.8);
}
.hero-title em{font-style:italic;color:var(--gold-lt)}
.hero-desc{
  color:rgba(250,249,245,.88);font-size:clamp(1.02rem,1.4vw,1.18rem);line-height:1.75;
  max-width:48ch;margin-bottom:2.5rem;
  text-shadow:0 1px 10px rgba(0,0,0,.6);
}
.hero-cta{display:flex;gap:1rem;flex-wrap:wrap}
.scroll-cue{
  position:absolute;z-index:2;right:var(--pad);bottom:1.75rem;
  display:flex;flex-direction:column;align-items:center;gap:.7rem;
  font-size:.66rem;font-weight:700;letter-spacing:.3em;text-transform:uppercase;
  color:rgba(250,249,245,.55);text-decoration:none;
  transition:color .3s var(--ease);
}
.scroll-cue:hover{color:var(--gold-lt)}
.scroll-cue::after{
  content:"";width:1px;height:44px;
  background:linear-gradient(180deg,var(--gold),transparent);
  animation:cueDrop 2.4s var(--ease) infinite;
}
@keyframes cueDrop{
  0%{transform:scaleY(0);transform-origin:top}
  45%{transform:scaleY(1);transform-origin:top}
  55%{transform:scaleY(1);transform-origin:bottom}
  100%{transform:scaleY(0);transform-origin:bottom}
}

/* ---------- stats strip ---------- */
.stats-wrap{position:relative;z-index:3;margin-top:-4.25rem;padding-bottom:0}
.stats-bar{
  background:rgba(23,26,23,.78);
  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  border:1px solid var(--line-d-soft);border-radius:10px;
  display:grid;grid-template-columns:repeat(4,1fr);
  padding:clamp(1.3rem,2.2vw,1.8rem) clamp(1.2rem,2.5vw,2.4rem);
  gap:1.25rem;
}
.stat{display:flex;align-items:baseline;gap:.85rem;min-width:0}
.stat + .stat{border-left:1px solid var(--line-d-soft);padding-left:1.5rem}
.stat-num{
  font-family:var(--serif);font-size:clamp(1.7rem,2.4vw,2.3rem);
  color:var(--gold-lt);line-height:1.1;white-space:nowrap;
}
.stat-lbl{
  font-size:.7rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase;
  color:var(--mut);line-height:1.6;
}

/* ---------- section headings ---------- */
.sec-over{
  font-size:.8rem;font-weight:700;letter-spacing:.34em;text-transform:uppercase;
  color:var(--gold-lt);margin-bottom:1.1rem;
}
.sec-title{
  font-family:var(--serif);font-weight:400;
  font-size:clamp(2.1rem,4.4vw,3.6rem);line-height:1.12;letter-spacing:-.01em;
  margin-bottom:1.2rem;max-width:20ch;
}
.sec-title em{font-style:italic}
.sec-light .sec-title{color:var(--ink-text)}
.sec-sub{color:var(--mut);max-width:56ch;font-size:1.02rem}
.sec-light .sec-sub{color:var(--mut-d)}
.sec-head{display:flex;align-items:flex-end;justify-content:space-between;
  gap:2rem;flex-wrap:wrap;margin-bottom:clamp(2.6rem,4.5vw,4rem)}
.sec-head .btn{flex:none}

/* ---------- featured projects ---------- */
.proj-grid{display:grid;grid-template-columns:repeat(12,1fr);
  gap:clamp(1.2rem,2.4vw,2rem);align-items:start}
.pcard{grid-column:span 6;text-decoration:none;display:block;min-width:0}
.pcard:first-child{grid-column:span 7}
.pcard:nth-child(2){grid-column:span 5}
.pcard:nth-child(3){grid-column:span 5}
.pcard:nth-child(4){grid-column:span 7}
.pcard-media{
  position:relative;overflow:hidden;border-radius:var(--radius);
  aspect-ratio:16/10;background:#E4DFD3;
}
.pcard:first-child .pcard-media,.pcard:nth-child(4) .pcard-media{aspect-ratio:16/11}
.pcard-media img{width:100%;height:100%;object-fit:cover;
  transition:transform 1.1s var(--ease)}
.pcard:hover .pcard-media img{transform:scale(1.045)}
.pcard-shade{
  position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(180deg,transparent 45%,rgba(10,10,10,.72) 100%);
}
.pcard-body{position:absolute;left:0;right:0;bottom:0;padding:1.4rem 1.5rem;
  display:flex;align-items:flex-end;justify-content:space-between;gap:1rem}
.pcard-name{font-family:var(--serif);font-size:clamp(1.25rem,2vw,1.7rem);
  color:var(--white);line-height:1.25}
.pcard-loc{font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;
  color:rgba(255,255,255,.72);margin-top:.35rem}
.pcard-go{
  flex:none;width:44px;height:44px;border-radius:50%;
  border:1px solid rgba(255,255,255,.35);display:flex;align-items:center;justify-content:center;
  color:var(--white);font-size:1.05rem;transition:.3s var(--ease);
  background:rgba(10,10,10,.35);backdrop-filter:blur(6px);
}
.pcard:hover .pcard-go{background:var(--gold);border-color:var(--gold);color:var(--black)}

/* ---------- services ---------- */
.svc-grid{display:grid;grid-template-columns:repeat(5,1fr);
  gap:clamp(1rem,1.8vw,1.5rem)}
.svc{
  background:var(--card);border:1px solid var(--line-d-soft);border-radius:var(--radius);
  padding:2.2rem 1.6rem;min-width:0;
  transition:border-color .35s var(--ease),transform .35s var(--ease),background .35s;
}
.svc:hover{border-color:rgba(201,169,97,.45);transform:translateY(-6px);background:var(--card-2)}
.svc-ico{
  width:52px;height:52px;border-radius:12px;margin-bottom:1.4rem;
  border:1px solid rgba(201,169,97,.35);display:flex;align-items:center;justify-content:center;
  color:var(--gold);font-size:1.5rem;
}
.svc h3{font-family:var(--serif);font-weight:400;font-size:1.3rem;margin-bottom:.7rem;color:var(--white)}
.svc p{font-size:.92rem;color:var(--mut);line-height:1.7}

/* ---------- process ---------- */
.steps{display:grid;grid-template-columns:repeat(5,1fr);
  gap:clamp(1.4rem,2.4vw,2.2rem);margin-top:clamp(2.4rem,4vw,3.6rem)}
.step{min-width:0}
.step-num{
  width:52px;height:52px;border-radius:50%;background:var(--gold);color:var(--black);
  display:flex;align-items:center;justify-content:center;
  font-weight:700;font-size:.95rem;letter-spacing:.05em;margin-bottom:1.3rem;
}
.step h3{font-family:var(--serif);font-weight:400;font-size:1.35rem;
  color:var(--ink-text);margin-bottom:.6rem}
.step p{font-size:.93rem;color:var(--mut-d);line-height:1.7}

/* ---------- insights ---------- */
.ins-grid{display:grid;grid-template-columns:repeat(3,1fr);
  gap:clamp(1.2rem,2.4vw,2rem)}
.ins-card{text-decoration:none;display:block;min-width:0}
.ins-media{overflow:hidden;border-radius:var(--radius);aspect-ratio:16/10;background:var(--card-2)}
.ins-media img{width:100%;height:100%;object-fit:cover;transition:transform 1.1s var(--ease)}
.ins-card:hover .ins-media img{transform:scale(1.045)}
.ins-date{font-size:.72rem;font-weight:700;letter-spacing:.24em;text-transform:uppercase;
  color:var(--gold);margin:1.3rem 0 .6rem}
.ins-card h3{font-family:var(--serif);font-weight:400;font-size:1.45rem;
  line-height:1.3;color:var(--white);margin-bottom:.8rem}
.ins-more{font-size:.78rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase;
  color:var(--mut);display:inline-flex;align-items:center;gap:.6em}
.ins-card:hover .ins-more{color:var(--gold)}

/* ---------- footer CTA ---------- */
.cta{
  position:relative;overflow:hidden;border-radius:calc(var(--radius) + 6px);
  margin-inline:var(--pad);max-width:var(--wrap);
}
.cta-bg{position:absolute;inset:0}
.cta-bg img{width:100%;height:100%;object-fit:cover}
.cta-shade{position:absolute;inset:0;background:rgba(10,10,10,.72)}
.cta-inner{
  position:relative;z-index:2;display:grid;grid-template-columns:1.1fr .9fr;
  gap:3rem;align-items:center;padding:clamp(3.5rem,6vw,6rem) clamp(2rem,4vw,4rem);
}
.cta h2{font-family:var(--serif);font-weight:400;
  font-size:clamp(2.2rem,4.6vw,3.8rem);line-height:1.1;color:var(--white);margin-bottom:1.8rem}
.cta h2 em{font-style:italic;color:var(--gold-lt)}
.cta-info{display:flex;flex-direction:column;gap:1rem;color:var(--mut);font-size:.98rem}
.cta-info a{color:var(--white);text-decoration:none}
.cta-info a:hover{color:var(--gold)}
.cta-form-note{font-size:.85rem;color:var(--mut-soft)}

/* ---------- footer ---------- */
.site-footer{background:#070707;border-top:1px solid var(--line-d-soft);
  padding:clamp(3.5rem,6vw,5.5rem) 0 2rem}
.foot-top{display:flex;align-items:flex-start;justify-content:space-between;
  gap:2.5rem;flex-wrap:wrap;margin-bottom:3rem}
.foot-word{font-family:var(--serif);font-size:clamp(1.8rem,3vw,2.6rem);
  letter-spacing:.12em;color:var(--white);text-decoration:none}
.foot-word .wm-dot{color:var(--gold)}
.foot-cols{display:flex;gap:clamp(2rem,5vw,5rem);flex-wrap:wrap}
.foot-col h4{font-size:.72rem;font-weight:700;letter-spacing:.28em;
  text-transform:uppercase;color:var(--gold);margin-bottom:1.1rem}
.foot-col a,.foot-col p{display:block;color:var(--mut);text-decoration:none;
  font-size:.95rem;margin-bottom:.55rem}
.foot-col a:hover{color:var(--white)}
.foot-base{display:flex;align-items:center;justify-content:space-between;
  gap:1rem;flex-wrap:wrap;padding-top:1.8rem;border-top:1px solid var(--line-d-soft);
  color:var(--mut-soft);font-size:.82rem}
.foot-base nav{display:flex;gap:1.6rem}
.foot-base a{color:var(--mut-soft);text-decoration:none}
.foot-base a:hover{color:var(--white)}

/* ---------- project pages — ARCOVA dark luxury ---------- */
.proj{background:var(--black);color:var(--white)}

/* breadcrumb bar */
.p-top{
  display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;
  padding-top:calc(76px + clamp(1.5rem,3vw,2.5rem));padding-bottom:1.2rem;
}
.p-top a{
  font-size:.78rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase;
  color:var(--mut);text-decoration:none;transition:color .3s var(--ease);
}
.p-top a:hover{color:var(--gold)}
.p-top .p-num{
  font-size:.78rem;letter-spacing:.18em;text-transform:uppercase;color:var(--mut-soft);
}

/* hero — cinematic full-bleed image with title overlay */
.p-hero{position:relative;min-height:72svh;display:flex;align-items:flex-end;overflow:hidden}
.p-hero .p-hero-media{position:absolute;inset:0}
.p-hero .p-hero-media img{width:100%;height:100%;object-fit:cover}
.p-hero .p-hero-scrim{
  position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(180deg,rgba(10,10,10,.5) 0%,rgba(10,10,10,.2) 35%,
    rgba(10,10,10,.7) 65%,rgba(10,10,10,.96) 100%);
}
.p-hero-copy{
  position:relative;z-index:2;width:100%;max-width:var(--wrap);
  margin-inline:auto;padding-inline:var(--pad);
  padding-bottom:clamp(3rem,6vw,5rem);padding-top:6rem;
}
.p-hero-over{
  font-size:.82rem;font-weight:700;letter-spacing:.36em;text-transform:uppercase;
  color:var(--gold-lt);margin-bottom:1.2rem;
  text-shadow:0 1px 8px rgba(0,0,0,.7);
}
.p-hero-title{
  font-family:var(--serif);font-weight:400;
  font-size:clamp(2.4rem,5.6vw,4.8rem);line-height:1.06;letter-spacing:-.01em;
  color:var(--white);max-width:16ch;
  text-shadow:0 2px 20px rgba(0,0,0,.65),0 1px 6px rgba(0,0,0,.8);
}
.p-hero-title em{font-style:italic;color:var(--gold-lt)}

/* intro — title, lede, meta grid */
.p-intro{background:var(--black);padding-block:clamp(3.5rem,6vw,5.5rem)}
.p-lede{
  font-family:var(--serif);font-size:clamp(1.25rem,2.2vw,1.7rem);line-height:1.55;
  color:var(--white);max-width:62ch;margin-bottom:clamp(2.5rem,4vw,3.5rem);
}
.p-lede em{font-style:italic;color:var(--gold-lt)}
.p-meta{
  display:grid;grid-template-columns:repeat(4,1fr);gap:1.8rem;
  border-top:1px solid var(--line-d-soft);padding-top:2rem;
}
.p-meta > div{min-width:0}
.p-meta dt{
  font-size:.72rem;font-weight:700;letter-spacing:.24em;text-transform:uppercase;
  color:var(--gold);margin-bottom:.6rem;
}
.p-meta dd{font-size:1rem;color:var(--mut);line-height:1.6}

/* chapters — numbered editorial sections */
.chapter{background:var(--black);padding-block:clamp(3rem,5vw,4.5rem)}
.chapter.alt{background:var(--ink)}
.ch-head{margin-bottom:clamp(2rem,3.5vw,3rem);max-width:70ch}
.ch-num{
  display:block;font-family:var(--serif);font-style:italic;
  font-size:clamp(1rem,1.6vw,1.25rem);color:var(--gold);margin-bottom:1rem;
}
.ch-head h2{
  font-family:var(--serif);font-weight:400;
  font-size:clamp(1.8rem,3.4vw,2.8rem);line-height:1.15;letter-spacing:-.01em;
  color:var(--white);margin-bottom:1.2rem;
}
.ch-head h2 em{font-style:italic;color:var(--gold-lt)}
.ch-body{color:var(--mut);font-size:1.02rem;line-height:1.8;max-width:62ch}
.ch-body p + p{margin-top:1.1rem}
.draw-tag{
  display:inline-block;margin-top:1.4rem;font-size:.72rem;font-weight:700;
  letter-spacing:.24em;text-transform:uppercase;color:var(--gold);
  border:1px solid rgba(201,169,97,.4);border-radius:999px;padding:.55rem 1.15rem;
}

/* chapter galleries */
.gal{display:grid;gap:clamp(1rem,2vw,1.6rem)}
.gal-pair{grid-template-columns:repeat(2,1fr)}
.gal-triple{grid-template-columns:repeat(3,1fr)}
.gal-single{grid-template-columns:1fr;max-width:1100px}
.gal-stack{grid-template-columns:1fr;max-width:900px;margin-inline:auto}
.gal-essay{grid-template-columns:1fr;max-width:1000px}
.g-fig{margin:0;min-width:0}
.g-fig button{
  all:unset;display:block;width:100%;cursor:zoom-in;border-radius:var(--radius);
  overflow:hidden;
}
.g-fig button:focus-visible{outline:2px solid var(--gold);outline-offset:4px}
.g-media{display:block;overflow:hidden;border-radius:var(--radius);background:var(--card)}
.g-media img{width:100%;height:100%;object-fit:cover;transition:transform .8s var(--ease)}
.g-fig button:hover .g-media img{transform:scale(1.03)}
.g-fig figcaption{
  margin-top:.9rem;font-size:.82rem;color:var(--mut-soft);letter-spacing:.04em;line-height:1.6;
}

/* related projects */
.related{background:var(--ink);border-top:1px solid var(--line-d-soft)}
.rel-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:clamp(1.2rem,2.4vw,2rem);margin-top:2.5rem}
.rel-card{
  display:block;text-decoration:none;color:inherit;min-width:0;
  background:var(--card);border:1px solid var(--line-d-soft);border-radius:var(--radius);
  overflow:hidden;transition:transform .4s var(--ease),border-color .4s var(--ease);
}
.rel-card:hover{transform:translateY(-6px);border-color:rgba(201,169,97,.35)}
.rel-media{display:block;aspect-ratio:16/10;overflow:hidden;background:var(--card-2)}
.rel-media img{width:100%;height:100%;object-fit:cover;transition:transform .8s var(--ease)}
.rel-card:hover .rel-media img{transform:scale(1.05)}
.rel-card h3{
  font-family:var(--serif);font-weight:400;font-size:1.35rem;line-height:1.3;
  color:var(--white);padding:1.3rem 1.4rem .4rem;
}
.rel-card p{font-size:.85rem;color:var(--mut-soft);padding:0 1.4rem 1.4rem;letter-spacing:.04em}

/* next project — large image CTA */
.p-next{
  position:relative;display:flex;align-items:flex-end;min-height:62svh;
  text-decoration:none;overflow:hidden;color:var(--white);
}
.p-next-media{position:absolute;inset:0}
.p-next-media img{width:100%;height:100%;object-fit:cover;transition:transform 1.2s var(--ease)}
.p-next:hover .p-next-media img{transform:scale(1.04)}
.p-next::after{
  content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(180deg,rgba(10,10,10,.25) 0%,rgba(10,10,10,.55) 55%,rgba(10,10,10,.94) 100%);
}
.p-next-copy{
  position:relative;z-index:2;width:100%;max-width:var(--wrap);
  margin-inline:auto;padding-inline:var(--pad);
  padding-bottom:clamp(3rem,6vw,5rem);padding-top:6rem;
}
.p-next-copy .eyebrow{color:var(--gold)}
.p-next-copy h2{
  font-family:var(--serif);font-weight:400;
  font-size:clamp(2.2rem,5vw,4.2rem);line-height:1.08;color:var(--white);
  max-width:14ch;margin:1rem 0 1.4rem;
}
.p-next-go{
  display:inline-flex;align-items:center;gap:.7em;
  font-size:.78rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase;
  color:var(--gold);
}
.p-next-go .arr{transition:transform .3s var(--ease)}
.p-next:hover .p-next-go .arr{transform:translate(4px,-4px)}

/* project contact CTA */
.p-cta{background:var(--black);text-align:center;border-top:1px solid var(--line-d-soft)}
.p-cta .eyebrow{display:flex;justify-content:center}
.contact-title{
  font-family:var(--serif);font-weight:400;
  font-size:clamp(2rem,4.4vw,3.4rem);line-height:1.12;color:var(--white);
  margin:1rem 0 1.1rem;
}
.contact-title em{font-style:italic;color:var(--gold-lt)}
.contact-copy{color:var(--mut);max-width:52ch;margin:0 auto 2.2rem;font-size:1.02rem}

/* ---------- responsive ---------- */
@media(max-width:1100px){
  .svc-grid{grid-template-columns:repeat(3,1fr)}
  .steps{grid-template-columns:repeat(3,1fr)}
  .ins-grid{grid-template-columns:repeat(2,1fr)}
  .pcard,.pcard:first-child,.pcard:nth-child(2),.pcard:nth-child(3),.pcard:nth-child(4){grid-column:span 6}
  .cta-inner{grid-template-columns:1fr}
  .p-meta{grid-template-columns:repeat(2,1fr)}
  .rel-grid{grid-template-columns:repeat(2,1fr)}
  .gal-triple{grid-template-columns:repeat(2,1fr)}
}
@media(max-width:860px){
  .site-nav,.head-cta{display:none}
  .menu-btn{display:flex}
  .head-inner{height:68px}
  .hero-media img{object-position:64% 38%}
  .stats-bar{grid-template-columns:repeat(2,1fr)}
  .stat:nth-child(3){border-left:0;padding-left:0;border-top:1px solid var(--line-d-soft);padding-top:1.1rem}
  .stat:nth-child(4){border-top:1px solid var(--line-d-soft);padding-top:1.1rem}
  .svc-grid{grid-template-columns:repeat(2,1fr)}
  .gal-pair,.gal-triple{grid-template-columns:1fr}
}
@media(max-width:600px){
  .hero{min-height:100svh}
  .hero-media img{object-position:66% 36%}
  .hero-inner{padding-top:6.5rem;padding-bottom:9.5rem}
  .hero-title{font-size:clamp(2.5rem,11.5vw,3.4rem);max-width:11ch}
  .hero-desc{max-width:38ch}
  .scroll-cue{display:none}
  .stats-wrap{margin-top:-3.5rem}
  .stats-bar{grid-template-columns:repeat(2,1fr);padding:1.4rem 1.2rem;gap:1.1rem}
  .stat + .stat{border-left:0;padding-left:0}
  .stat:nth-child(3){border-top:1px solid var(--line-d-soft);padding-top:1.1rem}
  .stat:nth-child(4){border-top:1px solid var(--line-d-soft);padding-top:1.1rem}
  .proj-grid{grid-template-columns:1fr}
  .pcard,.pcard:first-child,.pcard:nth-child(2),.pcard:nth-child(3),.pcard:nth-child(4){grid-column:span 12}
  .svc-grid{grid-template-columns:1fr}
  .steps{grid-template-columns:1fr}
  .ins-grid{grid-template-columns:1fr}
  .hero-inner{padding-bottom:8.5rem}
  .cta{margin-inline:16px}
  .p-meta{grid-template-columns:1fr;gap:1.2rem}
  .rel-grid{grid-template-columns:1fr}
  .p-hero{min-height:58svh}
  .p-next{min-height:50svh}
}

@media(prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  .js [data-rv]{opacity:1;transform:none}
  *,*::before,*::after{transition-duration:.01ms !important;animation-duration:.01ms !important}
}

'''

# ---------------------------------------------------------------- scripts

JS = '''/* Ola Magdy — calm interactions. Vanilla JS. Respects prefers-reduced-motion. */
(function(){
"use strict";
var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
var doc = document.documentElement;

/* ---------- header state ---------- */
var header = document.getElementById('siteHeader');
function onScrollHeader(){
  header.classList.toggle('scrolled', window.scrollY > 40);
}
window.addEventListener('scroll', onScrollHeader, {passive:true});
onScrollHeader();

/* ---------- scroll progress hairline ---------- */
var bar = document.getElementById('progressBar');
function onScrollProgress(){
  var h = doc.scrollHeight - window.innerHeight;
  var v = h > 0 ? (window.scrollY / h) : 0;
  bar.style.transform = 'scaleX(' + v + ')';
}
window.addEventListener('scroll', onScrollProgress, {passive:true});
onScrollProgress();

/* ---------- mobile menu ---------- */
var menuBtn = document.getElementById('menuBtn');
var overlay = document.getElementById('menuOverlay');
var lastFocus = null;
function setMenu(open){
  lastFocus = lastFocus || document.activeElement;
  doc.classList.toggle('menu-open', open);
  document.body.classList.toggle('menu-open', open);
  overlay.hidden = !open;
  menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
  menuBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  if(open){
    var first = overlay.querySelector('a');
    if(first) first.focus();
  }else if(lastFocus && lastFocus.focus){
    lastFocus.focus(); lastFocus = null;
  }
}
menuBtn.addEventListener('click', function(){
  setMenu(overlay.hidden);
});
document.addEventListener('keydown', function(ev){
  if(ev.key === 'Escape' && !overlay.hidden) setMenu(false);
});
overlay.addEventListener('click', function(ev){
  if(ev.target.closest('a')) setMenu(false);
});

/* ---------- entrance reveals ---------- */
var rvEls = document.querySelectorAll('[data-rv]');
if('IntersectionObserver' in window && !reduce && rvEls.length){
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if(en.isIntersecting){ en.target.classList.add('in'); io.unobserve(en.target); }
    });
  }, {threshold:.12, rootMargin:'0px 0px -6% 0px'});
  rvEls.forEach(function(el){ io.observe(el); });
}else{
  rvEls.forEach(function(el){ el.classList.add('in'); });
}

/* ---------- lightbox ---------- */
var lb = document.getElementById('lightbox');
if(lb){
  var lbImg = lb.querySelector('.lb-img');
  var lbCap = lb.querySelector('.lb-cap');
  var lbCount = lb.querySelector('.lb-count');
  var items = [], idx = 0, opener = null;

  function collect(group){
    var scope = group ? document.querySelector('[data-lb-group="' + group + '"]') : document;
    return Array.prototype.slice.call(scope.querySelectorAll('[data-lb-item]'));
  }
  function show(i){
    idx = (i + items.length) % items.length;
    var it = items[idx];
    lbImg.src = it.getAttribute('data-full');
    lbImg.alt = it.getAttribute('data-alt') || '';
    lbCap.textContent = it.getAttribute('data-cap') || '';
    lbCount.textContent = (idx + 1) + ' / ' + items.length;
    [lb.querySelector('.lb-prev'), lb.querySelector('.lb-next')].forEach(function(b){
      b.style.display = items.length > 1 ? '' : 'none';
    });
  }
  function open(item){
    opener = document.activeElement;
    items = collect(item.getAttribute('data-lb-group'));
    lb.hidden = false;
    document.body.style.overflow = 'hidden';
    show(items.indexOf(item));
    lb.querySelector('.lb-close').focus();
  }
  function close(){
    lb.hidden = true;
    document.body.style.overflow = '';
    if(opener && opener.focus) opener.focus();
  }
  document.addEventListener('click', function(ev){
    var t = ev.target.closest('[data-lb-item]');
    if(t){ ev.preventDefault(); open(t); return; }
    var c = ev.target.closest('[data-lb]');
    if(c && lb.hidden === false){
      var act = c.getAttribute('data-lb');
      if(act === 'close') close();
      else if(act === 'prev') show(idx - 1);
      else if(act === 'next') show(idx + 1);
    }
  });
  document.addEventListener('keydown', function(ev){
    if(lb.hidden) return;
    if(ev.key === 'Escape') close();
    else if(ev.key === 'ArrowLeft') show(idx - 1);
    else if(ev.key === 'ArrowRight') show(idx + 1);
    else if(ev.key === 'Tab'){ /* focus trap */
      var f = lb.querySelectorAll('button');
      var first = f[0], last = f[f.length - 1];
      if(ev.shiftKey && document.activeElement === first){ ev.preventDefault(); last.focus(); }
      else if(!ev.shiftKey && document.activeElement === last){ ev.preventDefault(); first.focus(); }
    }
  });
  var tx = null;
  lb.addEventListener('touchstart', function(ev){ tx = ev.touches[0].clientX; }, {passive:true});
  lb.addEventListener('touchend', function(ev){
    if(tx === null) return;
    var dx = ev.changedTouches[0].clientX - tx;
    if(Math.abs(dx) > 48) show(idx + (dx < 0 ? 1 : -1));
    tx = null;
  }, {passive:true});
}

/* ---------- project index: search + filter ---------- */
var searchInput = document.getElementById('project-search');
if(searchInput){
  var cards = Array.prototype.slice.call(document.querySelectorAll('[data-idx-card]'));
  var chips = Array.prototype.slice.call(document.querySelectorAll('[data-chip]'));
  var status = document.querySelector('.idx-status');
  var noRes = document.querySelector('.no-results');
  var activeCat = 'All';
  function apply(){
    var q = searchInput.value.trim().toLowerCase();
    var n = 0;
    cards.forEach(function(card){
      var okCat = activeCat === 'All' || card.getAttribute('data-cat') === activeCat;
      var hay = card.getAttribute('data-search').toLowerCase();
      var okQ = !q || hay.indexOf(q) !== -1;
      var show = okCat && okQ;
      card.hidden = !show;
      if(show) n++;
    });
    if(noRes) noRes.hidden = n !== 0;
    if(status) status.textContent = n + (n === 1 ? ' project' : ' projects');
  }
  var deb = null;
  searchInput.addEventListener('input', function(){
    clearTimeout(deb); deb = setTimeout(apply, 120);
  });
  chips.forEach(function(chip){
    chip.addEventListener('click', function(){
      activeCat = chip.getAttribute('data-chip');
      chips.forEach(function(c){ c.setAttribute('aria-pressed', c === chip ? 'true' : 'false'); });
      apply();
    });
  });
  apply();
}
})();
'''

# ---------------------------------------------------------------- homepage

def em_last(text):
    """Escape and italicise the final word (editorial headline treatment)."""
    words = e(text).rsplit(' ', 1)
    if len(words) == 2:
        return f'{words[0]} <em>{words[1]}</em>'
    return f'<em>{words[0]}</em>'



def em_last(text):
    """Escape and italicise the final word (editorial headline treatment)."""
    words = e(text).rsplit(' ', 1)
    if len(words) == 2:
        return f'{words[0]} <em>{words[1]}</em>'
    return f'<em>{words[0]}</em>'


# Curated "Selected works": display name -> real project id (images + links).
SELECTED_WORKS = [
    {'name': 'Sitra Cultural & Experience Centre',
     'meta': 'CULTURAL \u00b7 BAHRAIN', 'id': 'sohra-culture'},
    {'name': 'Pallial Care & Wellbeing',
     'meta': 'HEALTHCARE \u00b7 SAUDI ARABIA', 'id': 'palliative-care'},
    {'name': 'Ummar Lake',
     'meta': 'LANDSCAPE \u00b7 SAUDI ARABIA', 'id': 'umiam-lake'},
    {'name': 'Munjab Cultural Cause',
     'meta': 'CULTURAL \u00b7 SAUDI ARABIA', 'id': 'mandalgre'},
]

# Project index table: (num, project, type, location, year, project_id).
INDEX_ROWS = [
    ('01', 'Sitra Cultural & Experience Centre', 'Cultural', 'Bahrain',
     '2025', 'sohra-culture'),
    ('02', 'Pallial Care & Wellbeing', 'Healthcare', 'Riyadh, KSA',
     '2024', 'palliative-care'),
    ('03', 'Ummar Lake', 'Landscape', 'Ummar, KSA',
     '2023', 'umiam-lake'),
    ('04', 'Munjab Cultural Cause', 'Cultural', 'Munjab, KSA',
     '2021', 'mandalgre'),
]

# "In dialogue with the landscape": (asset key, caption, project).
FIELD_ITEMS = [
    ('d34s019i0', 'Masterplan', 'Sohra Culture & Experience Centre'),
    ('d01s030i0', 'Aerial view', 'Umiam Lake'),
    ('d49s037i0', 'Physical model', 'Bodoland Farmers\u2019 Market'),
    ('d37s024i0', 'Concept render', 'Tura Promenade & City Projects'),
    ('d24s028i0', 'Elevation study', 'Palliative Care & Housing'),
    ('d21s026i0', 'Architectural render', 'Mandalgre Cultural Centre'),
    ('d34s030i0', 'Landscape view', 'Sohra Culture & Experience Centre'),
    ('d21s016i0', 'Section study', 'Mandalgre Cultural Centre'),
]

# Selected publications & recognition: (year, outlet, project, note).
PUBLICATIONS = [
    ('2025', 'ArchDaily', 'Sitra Cultural & Experience Centre',
     'Featured Project'),
    ('2024', 'Dezeen', 'Pallial Care & Wellbeing', 'Longlist'),
    ('2023', 'World Architecture Festival', '',
     'Finalist \u2014 Health Category'),
]
PUB_QUOTE = ('\u201cA thoughtful and poetic approach to landscape and '
             'architecture.\u201d', 'World Architecture Festival, 2023')




# ---------------------------------------------------------------- ARCOVA sections

GOLD_ARROW = '<span class="arr" aria-hidden="true">&rarr;</span>'


def hero_section(p):
    h = SITE['hero']
    fallback = ORDERED[0] if ORDERED else GROUPS['sohra-culture']
    key = h['image'] if asset(h['image']) else fallback['hero']
    g = GROUPS.get(h.get('project_id')) or fallback
    return f"""<section class="hero" aria-labelledby="home-title">
  <div class="hero-media">{img(key, h.get('alt') or g['title'], eager=True)}</div>
  <div class="hero-scrim" aria-hidden="true"></div>
  <div class="hero-inner">
    <p class="hero-over" data-rv>Architecture &middot; Landscape &middot; Place</p>
    <h1 id="home-title" class="hero-title" data-rv="d1">We Create <em>Timeless</em> Spaces.<br>Designed Around You.</h1>
    <p class="hero-desc" data-rv="d2">From concept to completion, we craft meaningful spaces that connect people, architecture, and place.</p>
    <div class="hero-cta" data-rv="d3">
      <a class="btn btn-gold" href="#work">Explore our work {GOLD_ARROW}</a>
    </div>
  </div>
  <a class="scroll-cue" href="#work" aria-label="Scroll to selected work"><span>Scroll</span></a>
</section>"""


def stats_section(p):
    stats = [
        ("27+", "Projects Completed"),
        ("03", "States Across India"),
        ("19", "Project Locations"),
        ("03", "Design Disciplines"),
    ]
    items = []
    for i, (num, lbl) in enumerate(stats):
        items.append(f"""<div class="stat" role="listitem" data-rv="d{i}">
      <p class="stat-num">{num}</p><p class="stat-lbl">{lbl}</p>
    </div>""")
    return f"""<div class="wrap stats-wrap">
  <div class="stats-bar" role="list" aria-label="Studio in numbers">
{chr(10).join(items)}
  </div>
</div>"""


def work_section(p):
    cards = []
    feats = [
        ('sohra-culture', 'Sohra Culture & Experience Centre', 'Sohra, Meghalaya'),
        ('palliative-care', 'Palliative Care & Housing', 'Muzaffarpur, Bihar'),
        ('umiam-lake', 'Umiam Lake', 'Umiam, Meghalaya'),
        ('mandalgre', 'Mandalgre Cultural Centre', 'Mandalgre, Meghalaya'),
    ]
    for i, (pid, name, loc) in enumerate(feats):
        g = GROUPS.get(pid)
        if g is None:
            warnings.append(f"featured project missing: {pid}")
            continue
        key = g.get('hero')
        href = f'{p}projects/{pid}/'
        cards.append(f"""<a class="pcard" href="{href}" data-rv="d{i}" aria-label="{e(name)} &mdash; view project">
      <span class="pcard-media">{img(key, name) if key else ''}<span class="pcard-shade" aria-hidden="true"></span>
        <span class="pcard-body">
          <span><span class="pcard-name">{e(name)}</span><span class="pcard-loc">{e(loc)}</span></span>
          <span class="pcard-go" aria-hidden="true">&nearr;</span>
        </span>
      </span>
    </a>""")
    return f"""<section class="sec sec-light" id="work" aria-labelledby="work-title">
  <div class="wrap">
    <div class="sec-head">
      <div data-rv>
        <p class="sec-over">Featured Projects</p>
        <h2 class="sec-title" id="work-title">Spaces That Define <em>Excellence</em></h2>
      </div>
      <a class="btn btn-outline-d" href="{p}project-index/" data-rv="d1">View all projects {GOLD_ARROW}</a>
    </div>
    <div class="proj-grid">
{chr(10).join(cards)}
    </div>
  </div>
</section>"""


SERVICES = [
    ("&#9670;", "Architecture", "Concept-driven designs that blend creativity and functionality."),
    ("&#9635;", "Landscape Design", "Living landscapes shaped by ecology, culture and place."),
    ("&#9673;", "Urban Design", "High-performance public spaces for modern communities."),
    ("&#9733;", "Masterplanning", "Beautiful, functional frameworks tailored to their context."),
    ("&#9671;", "Interiors", "Seamless execution from concept to completion."),
]


def services_section(p):
    cards = []
    for i, (ico, name, desc) in enumerate(SERVICES):
        cards.append(f"""<div class="svc" data-rv="d{i}">
      <span class="svc-ico" aria-hidden="true">{ico}</span>
      <h3>{name}</h3>
      <p>{desc}</p>
    </div>""")
    return f"""<section class="sec sec-dark" id="services" aria-labelledby="svc-title">
  <div class="wrap">
    <div class="sec-head">
      <div data-rv>
        <p class="sec-over">Our Services</p>
        <h2 class="sec-title" id="svc-title">End-to-End <em>Solutions</em></h2>
        <p class="sec-sub">Integrated expertise across every stage of design and construction.</p>
      </div>
      <a class="btn btn-outline" href="#approach" data-rv="d1">Explore services {GOLD_ARROW}</a>
    </div>
    <div class="svc-grid">
{chr(10).join(cards)}
    </div>
  </div>
</section>"""


PROCESS_STEPS = [
    ("01", "Discover", "Understanding your vision, goals, and requirements."),
    ("02", "Design", "Crafting intelligent designs that inspire and perform."),
    ("03", "Build", "Expert construction with quality and precision."),
    ("04", "Deliver", "On-time delivery with attention to every detail."),
    ("05", "Beyond", "Ongoing support to ensure lasting satisfaction."),
]


def process_section(p):
    steps = []
    for i, (num, name, desc) in enumerate(PROCESS_STEPS):
        steps.append(f"""<div class="step" data-rv="d{i}">
      <span class="step-num" aria-hidden="true">{num}</span>
      <h3>{name}</h3>
      <p>{desc}</p>
    </div>""")
    return f"""<section class="sec sec-light" id="approach" aria-labelledby="proc-title">
  <div class="wrap">
    <div class="sec-head">
      <div data-rv>
        <p class="sec-over">Our Process</p>
        <h2 class="sec-title" id="proc-title">A Seamless Journey From Vision to Reality</h2>
      </div>
      <a class="btn btn-outline-d" href="#approach" data-rv="d1">How we work</a>
    </div>
    <div class="steps">
{chr(10).join(steps)}
    </div>
  </div>
</section>"""


def insights_section(p):
    spots = [
        ('sohra-culture', 'Sohra Culture & Experience Centre', 'Culture &middot; Meghalaya', 'Project Spotlight'),
        ('umiam-lake', 'Umiam Lake', 'Landscape &middot; Meghalaya', 'Project Spotlight'),
        ('palliative-care', 'Palliative Care & Housing', 'Healthcare &middot; Bihar', 'Project Spotlight'),
    ]
    cards = []
    for i, (pid, name, meta, tag) in enumerate(spots):
        g = GROUPS.get(pid)
        key = g.get('hero') if g else None
        href = f'{p}projects/{pid}/'
        cards.append(f"""<a class="ins-card" href="{href}" data-rv="d{i}" aria-label="{e(name)} &mdash; view project">
      <span class="ins-media">{img(key, name) if key else ''}</span>
      <p class="ins-date">{tag}</p>
      <h3>{e(name)}</h3>
      <span class="ins-more">Read more {GOLD_ARROW}</span>
    </a>""")
    return f"""<section class="sec sec-dark" id="journal" aria-labelledby="ins-title">
  <div class="wrap">
    <div class="sec-head">
      <div data-rv>
        <p class="sec-over">Insights</p>
        <h2 class="sec-title" id="ins-title">Ideas. Trends. <em>Inspiration.</em></h2>
      </div>
      <a class="btn btn-outline" href="{p}project-index/" data-rv="d1">View all articles {GOLD_ARROW}</a>
    </div>
    <div class="ins-grid">
{chr(10).join(cards)}
    </div>
  </div>
</section>"""


def contact_section(p):
    key = 'd34s027i0'
    email = SITE.get('contact', {}).get('email') or ''
    mail_html = f'<a href="mailto:{e(email)}">{e(email)}</a>' if email else ''
    return f"""<section class="sec sec-dark" id="contact" aria-labelledby="cta-title">
  <div class="cta" data-rv="clip">
    <div class="cta-bg" aria-hidden="true">{img(key, '') if asset(key) else ''}<span class="cta-shade"></span></div>
    <div class="cta-inner">
      <div>
        <h2 id="cta-title">Let&rsquo;s Build Something <em>Extraordinary</em></h2>
        <a class="btn btn-gold" href="mailto:{e(email)}" {" " if email else 'hidden'}>Start your project {GOLD_ARROW}</a>
      </div>
      <div class="cta-info">
        {mail_html}
        <p class="cta-form-note">We&rsquo;d love to hear about your project, idea, or opportunity to collaborate.</p>
      </div>
    </div>
  </div>
</section>"""



SECTION_BUILDERS = {
    'hero': lambda p: hero_section(p),
    'stats': lambda p: stats_section(p),
    'work': lambda p: work_section(p),
    'services': lambda p: services_section(p),
    'process': lambda p: process_section(p),
    'insights': lambda p: insights_section(p),
    'contact': lambda p: contact_section(p),
}


# ---------------------------------------------------------------- project pages

GAL_CLASS = {'single': 'gal-single', 'pair': 'gal-pair', 'triple': 'gal-triple',
             'stack': 'gal-stack', 'essay': 'gal-essay'}


def chapter_figure(key, cap, p, group):
    a = asset(key)
    if a is None:
        return ''
    return f'''<figure class="g-fig" data-rv>
  <button data-lb-item data-lb-group="{group}" data-full="{p}assets/{key}.webp"
          data-cap="{e(cap)}" data-alt="{e(cap)}"
          aria-label="Enlarge: {e(cap)}">
    <span class="g-media">{img(key, cap, p=p)}</span>
  </button>
  <figcaption>{e(cap)}</figcaption>
</figure>'''


def chapter_section(s, n, p, alt=False):
    captions = [s['captions']] if isinstance(s['captions'], str) else s['captions']
    if len(captions) != len(s['images']):
        warnings.append(f"caption count mismatch: {s.get('title')}")
    body = ''.join(f'<p>{e(para)}</p>'
                   for para in s['body'].split('\n\n') if para.strip())
    has_drawings = any(DRAWING_RE.search(c or '') for c in captions)
    tag = ('<span class="draw-tag">Drawings &amp; studies</span>'
           if has_drawings else '')
    gal_cls = GAL_CLASS.get(s.get('layout'), 'gal-pair')
    figs = '\n'.join(chapter_figure(k, cap, p, f'ch{n}')
                     for k, cap in zip(s['images'], captions))
    alt_cls = ' alt' if alt else ''
    return f'''<section class="chapter{alt_cls}" id="{e(s.get('anchor') or f'chapter-{n}')}"
         aria-labelledby="ch-title-{n}">
  <div class="wrap">
    <div class="ch-head">
      <span class="ch-num" data-rv>{str(n).zfill(2)}</span>
      <div>
        <h2 data-rv id="ch-title-{n}">{em_last(s['title'])}</h2>
        <div class="ch-body" data-rv="d1">{body}</div>
        <div data-rv="d1">{tag}</div>
      </div>
    </div>
    <div class="gal {gal_cls}" data-lb-group="ch{n}">
{figs}
    </div>
  </div>
</section>'''


def cta_band(p):
    c = SITE['contact']
    cta = ''
    if c.get('email'):
        cta = (f'<a class="btn btn-gold" data-rv href="mailto:{e(c["email"])}">'
               f'Get in touch {arrow()}</a>')
    return f'''<section class="p-cta sec">
  <div class="wrap">
    <p class="sec-over" data-rv style="justify-content:center">Contact</p>
    <h2 class="contact-title" data-rv>{em_last(c['headline'])}</h2>
    <p class="contact-copy" data-rv="d1">{e(c['copy'])}</p>
    {cta}
  </div>
</section>'''


def project_page(g, i, p='../../'):
    n = len(ORDERED)
    prev_g = ORDERED[(i - 1) % n]
    next_g = ORDERED[(i + 1) % n]
    rel = [ORDERED[(i + k) % n] for k in (1, 2, 3)]
    number = str(g['number']).zfill(2)

    chapters = '\n'.join(chapter_section(s, n_, p, alt=(n_ % 2 == 0))
                         for n_, s in enumerate(g['slides'], 1))
    rel_cards = '\n'.join(
        f'''<a class="rel-card" data-rv href="{p}projects/{r['id']}/">
      <span class="rel-media">{img(r['hero'], r['title'] + ' — design visualisation', p=p)}</span>
      <h3>{e(r['title'])}</h3>
      <p>{e(r['location'])}</p>
    </a>''' for r in rel)

    body = f'''<div class="p-top wrap">
  <a href="{p}project-index/">&larr; Project index</a>
  <span class="p-num">N&deg; {number} &mdash; {e(g['category'])}</span>
</div>
<section class="p-hero" aria-label="{e(g['title'])} &mdash; hero image">
  <div class="p-hero-media">{img(g['hero'], g['title'] + ' — design visualisation', eager=True, p=p)}</div>
  <div class="p-hero-scrim" aria-hidden="true"></div>
  <div class="p-hero-copy">
    <p class="p-hero-over" data-rv>{e(g['category'])} &middot; {e(g['location'])}</p>
    <h1 class="p-hero-title" data-rv="d1">{em_last(g['title'])}</h1>
  </div>
</section>
<section class="p-intro">
  <div class="wrap">
    <p class="p-lede" data-rv>{em_last(g['body'].strip())}</p>
    <dl class="p-meta" data-rv>
      <div><dt>Location</dt><dd>{e(g['location'])}</dd></div>
      <div><dt>Category</dt><dd>{e(g['category'])}</dd></div>
      <div><dt>Design role</dt><dd>Ola Magdy, Principal Associate Designer</dd></div>
      <div><dt>Practice</dt><dd>Archohm</dd></div>
    </dl>
  </div>
</section>
{chapters}
<section class="related sec">
  <div class="wrap">
    <p class="sec-over" data-rv>Related</p>
    <h2 class="sec-title" data-rv>Continue <em>exploring</em></h2>
    <div class="rel-grid">
{rel_cards}
    </div>
  </div>
</section>
<a class="p-next" href="{p}projects/{next_g['id']}/" data-rv="clip" aria-label="Next project: {e(next_g['title'])}">
  <span class="p-next-media rv-media">{img(next_g['hero'], next_g['title'] + ' — design visualisation', p=p)}</span>
  <span class="p-next-copy">
    <span class="sec-over">Next project &mdash; {str(next_g['number']).zfill(2)}</span>
    <h2>{em_last(next_g['title'])}</h2>
    <span class="p-next-go">View project {arrow()}</span>
  </span>
</a>
{cta_band(p)}'''
    desc = g['body'].strip()[:300]
    return shell(f"{g['title']} — Ola Magdy", desc, body,
                 p=p, page='proj', og_image=g['hero'])


# ---------------------------------------------------------------- project index

def index_page(p='../'):
    cats = []
    for g in ORDERED:
        if g['category'] not in cats:
            cats.append(g['category'])
    chips = ('<button class="chip" data-chip="All" aria-pressed="true">All</button>' +
             ''.join(f'<button class="chip" data-chip="{e(c)}" '
                     f'aria-pressed="false">{e(c)}</button>' for c in cats))
    cards = '\n'.join(
        f'''<a class="idx-card" data-rv href="{p}projects/{g['id']}/"
     data-idx-card data-cat="{e(g['category'])}"
     data-search="{e(g['title'])} {e(g['location'])} {e(g['category'])}"
     aria-label="{e(g['title'])} — view project">
      <span class="idx-media">{img(g['hero'], g['title'] + ' — design visualisation', p=p)}</span>
      <span class="idx-meta">{str(g['number']).zfill(2)} · {e(g['category'])}</span>
      <h2>{e(g['title'])}</h2>
      <span class="idx-loc">{e(g['location'])}</span>
    </a>''' for g in ORDERED)
    body = f'''<section class="idx-head sec">
  <div class="wrap">
    <p class="eyebrow" data-rv>The complete portfolio</p>
    <h1 class="sec-title" data-rv>Project <em>index</em></h1>
    <p class="sec-note" data-rv>Twenty-seven projects across architecture, landscape and urban design — from Meghalaya and Bihar to Bodoland.</p>
    <div class="idx-tools" data-rv="d1">
      <div class="idx-search">
        <label for="project-search">Search projects</label>
        <input id="project-search" type="search" placeholder="Try Umiam, market or healthcare…"
               autocomplete="off">
      </div>
      <div class="idx-filters" role="group" aria-label="Filter by category">
        {chips}
      </div>
      <p class="idx-status" role="status" aria-live="polite"></p>
    </div>
  </div>
</section>
<section aria-label="Projects">
  <div class="wrap idx-grid">
{cards}
    <p class="no-results" hidden>No matching projects. Try a different name, programme or place.</p>
  </div>
</section>'''
    return shell('Project Index — Ola Magdy',
                 'Explore the complete portfolio: 27 architecture, landscape and '
                 'urban design projects across Meghalaya, Bihar and Bodoland.',
                 body, p=p, page='idx-page')

# ---------------------------------------------------------------- assemble

def build_homepage():
    parts = []
    disabled = set(SITE.get('sections_disabled') or [])
    for name in SITE.get('sections_order', []):
        if name in disabled:
            continue
        fn = SECTION_BUILDERS.get(name)
        if fn is None:
            warnings.append(f'unknown section in sections_order: {name}')
            continue
        parts.append(fn(''))
    body = '\n'.join(p for p in parts if p)
    seo = SITE.get('seo', {})
    return shell(seo.get('title', 'Ola Magdy'),
                 seo.get('description', ''),
                 body, p='', page='home')


def main():
    D.mkdir(exist_ok=True)
    (D / 'style.css').write_text(CSS, encoding='utf-8')
    (D / 'site.js').write_text(JS, encoding='utf-8')
    print('style.css + site.js written')

    (D / 'index.html').write_text(build_homepage(), encoding='utf-8')
    print('homepage written')

    for i, g in enumerate(ORDERED):
        out = D / 'projects' / g['id']
        out.mkdir(parents=True, exist_ok=True)
        (out / 'index.html').write_text(project_page(g, i), encoding='utf-8')
    print(f'{len(ORDERED)} project pages written')

    # Remove stale project dirs (unpublished / renamed projects).
    live = {g['id'] for g in ORDERED}
    for d in (D / 'projects').iterdir():
        if d.is_dir() and d.name not in live:
            shutil.rmtree(d)
            print(f'removed stale: projects/{d.name}/')

    idx = D / 'project-index'
    idx.mkdir(parents=True, exist_ok=True)
    (idx / 'index.html').write_text(index_page(), encoding='utf-8')
    print('project index written')

    verify()
    if warnings:
        print(f'\n{len(warnings)} warning(s):')
        for w in warnings[:20]:
            print('  -', w)
    print(f'\n(site content: {site_src})')


# ---------------------------------------------------------------- verify

ABS_RE = re.compile(r'''(?:href|src)\s*=\s*["']/(?!/)|url\(\s*['"]?/''')
EXT_RE = re.compile(r'^(?:https?:|mailto:|tel:|data:|#)')


def verify():
    pages = [D / 'index.html', D / 'project-index' / 'index.html']
    pages += [D / 'projects' / g['id'] / 'index.html' for g in ORDERED]
    expected = 2 + len(ORDERED)  # home + index + one page per published project
    assert len(pages) == expected, f'expected {expected} pages, got {len(pages)}'
    for pg in pages:
        assert pg.exists(), f'missing page: {pg}'

    href_re = re.compile(r'''(?:href|src)\s*=\s*["']([^"']+)["']''')
    errors, checked, asset_refs = 0, 0, set()
    for pg in pages:
        text = pg.read_text(encoding='utf-8')
        if ABS_RE.search(text):
            print(f'  ERROR: root-absolute path in {pg.relative_to(D)}')
            errors += 1
        for m in href_re.finditer(text):
            url = m.group(1)
            if EXT_RE.match(url) or url.startswith('https://olamagdy.example/'):
                continue
            checked += 1
            url = url.split('#')[0].split('?')[0]
            if not url:
                continue  # same-page anchor
            target = (pg.parent / url).resolve()
            ok = target.is_file() or (target.is_dir()
                                     and (target / 'index.html').is_file())
            if not ok:
                print(f'  ERROR: broken link {url} in {pg.relative_to(D)}')
                errors += 1
            if '/assets/' in url and url.endswith('.webp'):
                asset_refs.add(target.name.replace('.webp', ''))

    missing_assets = [k for k in asset_refs if not (D / 'assets' / f'{k}.webp').exists()]
    if missing_assets:
        print(f'  ERROR: missing asset files: {missing_assets[:5]}')
        errors += len(missing_assets)

    # every project hero + slide image must be reachable from some page
    print(f'checked {checked} links across {len(pages)} pages; '
          f'{len(asset_refs)} distinct assets referenced')
    if errors:
        raise SystemExit(f'VERIFY FAILED: {errors} error(s)')
    print('verify: all links resolve, no missing assets, no root-absolute paths')


if __name__ == '__main__':
    main()
