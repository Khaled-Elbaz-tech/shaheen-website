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
ASSET_V = "5"

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
  <a class="wordmark" href="{p}" aria-label="Ola Magdy — home">Ola&nbsp;Magdy</a>
  <nav class="site-nav" aria-label="Primary">
    {nav_items(p)}
  </nav>
  <button class="menu-btn" id="menuBtn" aria-expanded="false"
          aria-controls="menuOverlay" aria-label="Open menu">
    <span></span><span></span>
  </button>
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
    <div class="foot-grid">
      <a class="foot-word" href="{p}" aria-label="Ola Magdy — home">OLA&nbsp;MAGADY</a>
      <a class="foot-mail" href="mailto:{email}">{email}</a>
      <div class="foot-social" aria-label="Social profiles">
        <span>Instagram</span><span>LinkedIn</span><span>Behance</span>
      </div>
    </div>
    <div class="foot-base">
      <p>© 2029 OLA MAGADY. All rights reserved.</p>
      <p>Architecture · Landscape · Place</p>
    </div>
  </div>
</footer>
{lightbox_markup()}
</body>
</html>
'''

# ---------------------------------------------------------------- styles

CSS = '''/* Ola Magdy — Architecture, Landscape & Urbanism.
   Warm ivory / deep charcoal editorial system. Instrument Serif display,
   Manrope text. All asset URLs relative. */

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

:root{
  --ivory:#F2F0E9; --ivory-2:#EAE7DB; --paper:#F7F5EE;
  --ink:#171A17; --ink-2:#20241F; --ink-3:#2B302A;
  --olive:#6B6B4E; --olive-deep:#4C4C3A;
  --stone:#D8D2C4; --stone-deep:#B3AC99;
  --line:rgba(23,26,23,.16); --line-soft:rgba(23,26,23,.09);
  --line-l:rgba(242,240,233,.18); --line-l-soft:rgba(242,240,233,.10);
  --mut:#57564D; --mut-l:#B9B4A4;
  --serif:"Instrument Serif",Georgia,"Times New Roman",serif;
  --sans:"Manrope",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --wrap:1440px;
  --pad:clamp(20px,4vw,60px);
  --ease:cubic-bezier(.22,.61,.21,1);
}

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{
  font-family:var(--sans);font-weight:400;font-size:1.0625rem;line-height:1.7;
  color:var(--ink);background:var(--ivory);
  -webkit-font-smoothing:antialiased;overflow-x:hidden;
}
img{max-width:100%;height:auto;display:block}
a{color:inherit}
::selection{background:var(--olive);color:var(--ivory)}

:focus{outline:none}
:focus-visible{outline:2px solid var(--olive);outline-offset:3px;border-radius:2px}
.on-dark :focus-visible,.site-footer :focus-visible{outline-color:var(--stone)}

.skip{
  position:fixed;top:-60px;left:16px;z-index:200;background:var(--ink);
  color:var(--ivory);padding:.6rem 1.1rem;font-size:.85rem;text-decoration:none;
  border-radius:0 0 6px 6px;transition:top .2s var(--ease);
}
.skip:focus{top:0}

.wrap{max-width:var(--wrap);margin-inline:auto;padding-inline:var(--pad)}
.sec{padding-block:clamp(5rem,9vw,9.5rem)}

h1,h2,h3,.serif{font-family:var(--serif);font-weight:400;line-height:1.04;
  letter-spacing:-.01em;text-wrap:balance}
h1 em,h2 em,h3 em,.serif em{font-style:italic}

.eyebrow{
  font-size:.72rem;font-weight:600;letter-spacing:.24em;text-transform:uppercase;
  color:var(--olive);display:flex;align-items:center;gap:.9em;margin-bottom:1.6rem;
}
.eyebrow::before{content:"";width:2.6em;height:1px;background:currentColor;opacity:.7}
.on-dark .eyebrow{color:var(--stone)}
.eyebrow.light{color:var(--stone)}

.sec-title{font-size:clamp(2.6rem,5.4vw,4.9rem);max-width:14ch}
.sec-note{color:var(--mut);max-width:52ch;margin-top:1.4rem;font-size:1.05rem}
.on-dark .sec-note{color:var(--mut-l)}

/* ---------- motion: calm reveals ---------- */
.js [data-rv]{opacity:0;transform:translateY(30px);
  transition:opacity .9s var(--ease),transform .9s var(--ease)}
.js [data-rv].in{opacity:1;transform:none}
.js [data-rv="clip"] .rv-media{clip-path:inset(6% 4% 6% 4% round 2px);
  transition:clip-path 1.1s var(--ease)}
.js [data-rv="clip"].in .rv-media{clip-path:inset(0 0 0 0 round 2px)}
.js [data-rv="d1"]{transition-delay:.12s}
.js [data-rv="d2"]{transition-delay:.24s}

/* ---------- scroll progress ---------- */
.progress{position:fixed;top:0;left:0;right:0;height:2px;z-index:120;
  background:transparent;pointer-events:none}
.progress span{display:block;height:100%;width:100%;background:var(--olive);
  transform:scaleX(0);transform-origin:0 50%}

/* ---------- header ---------- */
.site-header{
  position:fixed;inset:0 0 auto 0;z-index:100;
  display:flex;align-items:center;justify-content:space-between;
  padding:1.15rem var(--pad);
  color:var(--ivory);
  transition:background .45s var(--ease),color .45s var(--ease),
             box-shadow .45s var(--ease),padding .45s var(--ease);
}
.site-header.scrolled{
  background:rgba(242,240,233,.92);color:var(--ink);
  -webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);
  box-shadow:0 1px 0 var(--line-soft);padding-block:.85rem;
}
body:not(.home) .site-header{background:rgba(242,240,233,.92);color:var(--ink);
  -webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);
  box-shadow:0 1px 0 var(--line-soft)}
.wordmark{
  font-size:.82rem;font-weight:600;letter-spacing:.34em;text-transform:uppercase;
  text-decoration:none;white-space:nowrap;
}
.site-nav{display:flex;align-items:center;gap:clamp(1.1rem,2.4vw,2.2rem)}
.nav-link{
  position:relative;text-decoration:none;font-size:.82rem;font-weight:600;
  letter-spacing:.16em;text-transform:uppercase;padding:.4rem 0;color:inherit;
}
.nav-link>span{position:relative}
.nav-link>span::after{
  content:"";position:absolute;left:0;bottom:-5px;height:1px;width:100%;
  background:currentColor;transform:scaleX(0);transform-origin:100% 50%;
  transition:transform .35s var(--ease);
}
.nav-link:hover>span::after,.nav-link:focus-visible>span::after{
  transform:scaleX(1);transform-origin:0 50%}
.nav-link .arr{font-size:.9em;margin-left:.3em}
.menu-btn{display:none}

/* mobile menu */
.menu-overlay{
  position:fixed;inset:0;z-index:90;background:var(--ivory);color:var(--ink);
  display:flex;flex-direction:column;justify-content:center;gap:.4rem;
  padding:5rem var(--pad) 3rem;
}
.menu-overlay[hidden]{display:none}
.menu-overlay nav{display:flex;flex-direction:column;gap:.2rem}
.menu-overlay .nav-link{font-family:var(--serif);font-size:clamp(2.4rem,9vw,3.6rem);
  letter-spacing:0;text-transform:none;font-weight:400;padding:.35rem 0}
.menu-overlay .nav-link>span::after{display:none}
.menu-note{margin-top:3rem;font-size:.8rem;letter-spacing:.18em;
  text-transform:uppercase;color:var(--mut)}
.menu-btn{
  background:none;border:0;cursor:pointer;width:44px;height:44px;
  position:relative;z-index:130;display:none;flex-direction:column;
  align-items:center;justify-content:center;gap:7px;color:inherit;
}
.menu-btn span{display:block;width:26px;height:1.5px;background:currentColor;
  transition:transform .35s var(--ease),opacity .3s}
body.menu-open{overflow:hidden}
body.menu-open .menu-btn span:first-child{transform:translateY(4.25px) rotate(45deg)}
body.menu-open .menu-btn span:last-child{transform:translateY(-4.25px) rotate(-45deg)}
body.menu-open .site-header{background:transparent;color:var(--ink);box-shadow:none}

/* ---------- hero ---------- */
.hero{position:relative;min-height:100svh;display:flex;align-items:flex-end;
  color:var(--ivory);overflow:hidden;background:var(--ink)}
.hero-media{position:absolute;inset:0}
.hero-media img{width:100%;height:100%;object-fit:cover;object-position:center 38%}
.hero-scrim{position:absolute;inset:0;background:
  linear-gradient(to top,rgba(15,17,15,.62) 0%,rgba(15,17,15,.18) 34%,transparent 58%),
  linear-gradient(to bottom,rgba(15,17,15,.30),transparent 26%)}
.hero-inner{position:relative;z-index:2;width:100%;padding-bottom:clamp(4.5rem,8vh,7rem)}
.hero-desc{font-size:.74rem;font-weight:600;letter-spacing:.3em;color:var(--stone);
  margin-bottom:1.4rem}
.hero-title{font-size:clamp(3.4rem,10.5vw,9.2rem);max-width:12ch;color:var(--ivory)}
.hero-foot{margin-top:2.2rem;display:flex;align-items:center;gap:1.6rem;flex-wrap:wrap}
.hero-cap-link{
  display:inline-flex;align-items:center;gap:.7em;text-decoration:none;
  border:1px solid rgba(242,240,233,.45);border-radius:999px;
  padding:.75rem 1.5rem;font-size:.8rem;font-weight:600;letter-spacing:.14em;
  text-transform:uppercase;color:var(--ivory);
  transition:background .35s var(--ease),border-color .35s;
}
.hero-cap-link:hover{background:rgba(242,240,233,.14);border-color:var(--ivory)}
.scroll-cue{
  position:absolute;right:var(--pad);bottom:clamp(4.5rem,8vh,7rem);z-index:2;
  display:flex;flex-direction:column;align-items:center;gap:.8rem;
  font-size:.68rem;letter-spacing:.3em;text-transform:uppercase;color:var(--stone);
  writing-mode:vertical-rl;
}
.scroll-cue i{width:1px;height:56px;background:rgba(216,210,196,.35);
  position:relative;overflow:hidden;display:block}
.scroll-cue i::after{content:"";position:absolute;left:0;top:-40%;width:100%;
  height:40%;background:var(--stone);animation:cue 2.2s var(--ease) infinite}
@keyframes cue{to{top:110%}}

/* ---------- intro ---------- */
.intro-statement{font-size:clamp(2rem,4.6vw,3.9rem);max-width:20ch;margin-bottom:2.4rem}
.intro-copy{max-width:62ch;color:var(--mut);font-size:1.12rem}
.intro-copy p+p{margin-top:1.2em}

/* ---------- work (charcoal) ---------- */
.work{background:var(--ink);color:var(--ivory)}
.work-head{display:flex;align-items:flex-end;justify-content:space-between;
  gap:2rem;flex-wrap:wrap;margin-bottom:clamp(3rem,5vw,4.5rem)}
.work-count{font-size:.78rem;letter-spacing:.22em;text-transform:uppercase;
  color:var(--mut-l);border:1px solid var(--line-l);border-radius:999px;
  padding:.6rem 1.2rem;white-space:nowrap}
.work-grid{display:grid;grid-template-columns:repeat(12,1fr);
  gap:clamp(2.2rem,4vw,4rem) clamp(1.4rem,2.5vw,2.6rem);align-items:start}
.wcard{grid-column:span 12;text-decoration:none;display:block}
.wcard-link-card{display:block;text-decoration:none;color:inherit}
@media(min-width:760px){
  .sp7{grid-column:span 7}.sp5{grid-column:span 5}
  .sp8{grid-column:span 8}.sp4{grid-column:span 4}.sp6{grid-column:span 6}
  .os{margin-top:clamp(3rem,7vw,7rem)}
}
.wcard-media{overflow:hidden;border-radius:2px;background:var(--ink-2)}
.wcard-media img{width:100%;transition:transform 1s var(--ease)}
.wcard:hover .wcard-media img,.wcard:focus-visible .wcard-media img{transform:scale(1.03)}
.wcard-meta{display:flex;align-items:baseline;gap:1.1rem;margin:1.3rem 0 .7rem;
  font-size:.74rem;font-weight:600;letter-spacing:.2em;text-transform:uppercase;
  color:var(--mut-l)}
.wcard-num{color:var(--olive);font-family:var(--serif);font-style:italic;
  font-size:1rem;letter-spacing:0}
.wcard-title{font-size:clamp(1.65rem,2.6vw,2.5rem);max-width:16ch}
.wcard-loc{margin-top:.55rem;color:var(--mut-l);font-size:.95rem}
.wcard-link{display:inline-flex;align-items:center;gap:.5em;margin-top:1rem;
  font-size:.78rem;font-weight:600;letter-spacing:.2em;text-transform:uppercase;
  color:var(--stone)}
.wcard-link .arr{transition:transform .3s var(--ease)}
.wcard:hover .wcard-link .arr{transform:translate(3px,-3px)}
.work-more{margin-top:clamp(3rem,5vw,4.5rem);text-align:center}

/* ---------- landscape gallery ---------- */
.field-grid{display:grid;grid-template-columns:repeat(12,1fr);
  gap:clamp(1.6rem,3vw,3rem) clamp(1.2rem,2.2vw,2.2rem);align-items:start}
.fcard{grid-column:span 12}
@media(min-width:760px){
  .f7{grid-column:span 7}.f5{grid-column:span 5}.f4{grid-column:span 4}
  .f8{grid-column:span 8}.f12{grid-column:span 12}
  .fos{margin-top:clamp(2.5rem,5vw,5rem)}
}
.fcard button{
  all:unset;display:block;width:100%;cursor:zoom-in;border-radius:2px;
}
.fcard button:focus-visible{outline:2px solid var(--olive);outline-offset:4px}
.fcard-media{overflow:hidden;border-radius:2px;background:var(--ivory-2)}
.fcard-media img{width:100%;transition:transform 1s var(--ease)}
.fcard button:hover .fcard-media img{transform:scale(1.03)}
.fcard figcaption{margin-top:.9rem;display:flex;justify-content:space-between;
  gap:1rem;align-items:baseline}
.fcard-cap{font-size:.95rem;color:var(--ink)}
.fcard-proj{font-size:.74rem;font-weight:600;letter-spacing:.16em;
  text-transform:uppercase;color:var(--mut);white-space:nowrap}

/* ---------- studio ---------- */
.studio{background:var(--paper);border-block:1px solid var(--line-soft)}
.studio-grid{display:grid;grid-template-columns:1fr;gap:clamp(2.5rem,5vw,5rem)}
@media(min-width:900px){
  .studio-grid{grid-template-columns:repeat(12,1fr);align-items:start}
  .studio-media{grid-column:1/span 5}
  .studio-copy{grid-column:7/span 6}
}
.studio-media .rv-media{overflow:hidden;border-radius:2px}
.studio-cap{margin-top:.9rem;font-size:.85rem;color:var(--mut);font-style:italic}
.studio-lede{font-family:var(--serif);font-size:clamp(1.5rem,2.4vw,2.1rem);
  line-height:1.35;margin:0 0 1.8rem;max-width:26ch}
.studio-bio p{margin-bottom:1.3em;color:#3E3D36;max-width:64ch}
.studio-philo{margin-top:2.6rem;padding-top:2.2rem;border-top:1px solid var(--line)}
.studio-philo p{font-family:var(--serif);font-style:italic;
  font-size:clamp(1.25rem,2vw,1.7rem);line-height:1.45;color:var(--olive-deep);
  max-width:30ch}

/* ---------- approach ---------- */
.approach{background:var(--ink);color:var(--ivory)}
.stages{display:grid;grid-template-columns:1fr;gap:0;margin-top:clamp(2.5rem,4vw,4rem)}
@media(min-width:900px){.stages{grid-template-columns:repeat(4,1fr);
  gap:clamp(1.5rem,2.5vw,2.8rem)}}
.stage{padding:2rem 0;border-top:1px solid var(--line-l)}
@media(min-width:900px){.stage{padding:1.8rem 0 0}}
.stage-num{font-family:var(--serif);font-style:italic;font-size:1rem;
  color:var(--olive);display:block;margin-bottom:1.1rem}
.stage h3{font-size:clamp(1.7rem,2.4vw,2.3rem);margin-bottom:1rem}
.stage p{color:var(--mut-l);font-size:1rem;max-width:32ch}

/* ---------- journal ---------- */
.journal-list{list-style:none;margin-top:2.5rem;border-top:1px solid var(--line)}
.journal-list li{border-bottom:1px solid var(--line)}
.journal-list a{display:grid;grid-template-columns:1fr;gap:.4rem;
  padding:1.8rem .2rem;text-decoration:none}
@media(min-width:760px){
  .journal-list a{grid-template-columns:11rem 1fr auto;gap:2rem;align-items:baseline}}
.j-date{font-size:.78rem;letter-spacing:.2em;text-transform:uppercase;color:var(--mut)}
.j-title{font-family:var(--serif);font-size:clamp(1.4rem,2.2vw,2rem)}
.j-sum{color:var(--mut);font-size:.98rem;max-width:60ch}
.journal-list a .arr{justify-self:end}

/* ---------- contact ---------- */
.contact{text-align:center}
.contact .eyebrow{justify-content:center}
.contact .eyebrow::after{content:"";width:2.6em;height:1px;
  background:currentColor;opacity:.7}
.contact-title{font-size:clamp(2.8rem,6.5vw,5.6rem);max-width:16ch;
  margin-inline:auto}
.contact-copy{color:var(--mut);max-width:52ch;margin:1.6rem auto 2.6rem;
  font-size:1.1rem}
.btn{
  display:inline-flex;align-items:center;gap:.7em;text-decoration:none;
  background:var(--ink);color:var(--ivory);border-radius:999px;
  padding:1.05rem 2.4rem;font-size:.84rem;font-weight:600;letter-spacing:.16em;
  text-transform:uppercase;transition:background .35s var(--ease),transform .35s var(--ease);
}
.btn:hover{background:var(--olive-deep);transform:translateY(-2px)}
.btn-ghost{background:transparent;color:var(--ivory);border:1px solid var(--line-l)}
.btn-ghost:hover{background:rgba(242,240,233,.12);border-color:var(--ivory)}

/* ---------- footer ---------- */
.site-footer{background:var(--ink);color:var(--ivory);border-top:1px solid var(--line-l-soft)}
.foot-inner{max-width:var(--wrap);margin-inline:auto;padding:clamp(3.5rem,6vw,5.5rem) var(--pad) 2.5rem}
.foot-top{display:flex;justify-content:space-between;align-items:flex-start;
  gap:2rem;flex-wrap:wrap;padding-bottom:2.5rem;border-bottom:1px solid var(--line-l-soft)}
.foot-word{font-family:var(--serif);font-size:clamp(2.6rem,6vw,4.6rem);
  text-decoration:none;line-height:1}
.foot-nav{display:flex;gap:1.6rem;flex-wrap:wrap;align-items:center}
.foot-nav .nav-link{font-size:.76rem}
.foot-meta{padding-top:2rem;display:grid;gap:.5rem;font-size:.9rem;color:var(--mut-l)}
.foot-copy{color:#8E8978;font-size:.82rem}
.to-top{display:inline-block;margin-top:1.8rem;font-size:.78rem;font-weight:600;
  letter-spacing:.2em;text-transform:uppercase;text-decoration:none;color:var(--stone)}

/* ---------- lightbox ---------- */
.lb{position:fixed;inset:0;z-index:150;display:flex;align-items:center;
  justify-content:center}
.lb[hidden]{display:none}
.lb-backdrop{position:absolute;inset:0;background:rgba(15,17,15,.96)}
.lb-figure{position:relative;z-index:2;max-width:min(92vw,1500px);
  max-height:86vh;display:flex;flex-direction:column}
.lb-img{max-width:100%;max-height:76vh;object-fit:contain;border-radius:2px}
.lb-cap{margin-top:1rem;color:var(--stone);font-size:.95rem;text-align:center;
  max-width:70ch}
.lb-count{position:absolute;bottom:2rem;left:50%;transform:translateX(-50%);
  color:var(--mut-l);font-size:.8rem;letter-spacing:.24em;z-index:2}
.lb-btn{position:absolute;z-index:3;background:transparent;border:1px solid var(--line-l);
  color:var(--ivory);width:52px;height:52px;border-radius:50%;cursor:pointer;
  font-size:1.25rem;display:flex;align-items:center;justify-content:center;
  transition:background .3s,border-color .3s}
.lb-btn:hover{background:rgba(242,240,233,.14);border-color:var(--ivory)}
.lb-prev{left:1.4rem;top:50%;transform:translateY(-50%)}
.lb-next{right:1.4rem;top:50%;transform:translateY(-50%)}
.lb-close{top:1.4rem;right:1.4rem}

/* ============================================================
   PROJECT PAGES
   ============================================================ */
.p-top{display:flex;justify-content:space-between;align-items:center;
  padding:calc(4.5rem + 1.2rem) var(--pad) 1.2rem;max-width:var(--wrap);margin-inline:auto;
  font-size:.78rem;font-weight:600;letter-spacing:.2em;text-transform:uppercase}
.p-top a{text-decoration:none;color:var(--mut)}
.p-top a:hover{color:var(--ink)}
.p-hero{position:relative;height:clamp(320px,72vh,760px);overflow:hidden;background:var(--ink-2)}
.p-hero img{width:100%;height:100%;object-fit:cover}
.p-head{padding-block:clamp(3rem,5vw,4.5rem)}
.p-loc{font-size:.76rem;font-weight:600;letter-spacing:.26em;text-transform:uppercase;
  color:var(--olive);margin-bottom:1.2rem}
.p-title{font-size:clamp(2.8rem,7vw,6.2rem);max-width:18ch}
.p-lede{font-family:var(--serif);font-size:clamp(1.35rem,2.4vw,1.9rem);
  line-height:1.5;max-width:44ch;margin-top:2rem;color:#33322C}
.p-meta{display:grid;grid-template-columns:repeat(2,1fr);gap:0;
  margin-top:3rem;border-top:1px solid var(--line)}
@media(min-width:760px){.p-meta{grid-template-columns:repeat(4,1fr)}}
.p-meta>div{padding:1.4rem 1.4rem 1.4rem 0;border-bottom:1px solid var(--line)}
.p-meta dt{font-size:.72rem;font-weight:600;letter-spacing:.22em;
  text-transform:uppercase;color:var(--mut);margin-bottom:.5rem}
.p-meta dd{font-family:var(--serif);font-size:1.25rem}

.chapter{padding-block:clamp(3rem,5vw,4.5rem);border-top:1px solid var(--line)}
.ch-head{display:grid;grid-template-columns:1fr;gap:1rem;margin-bottom:2.4rem}
@media(min-width:900px){.ch-head{grid-template-columns:7rem 1fr;gap:2.5rem}}
.ch-num{font-family:var(--serif);font-style:italic;font-size:1.1rem;color:var(--olive)}
.ch-head h2{font-size:clamp(1.9rem,3.6vw,3rem);max-width:22ch}
.ch-body{color:#3E3D36;max-width:68ch;margin-top:1.2rem;font-size:1.06rem}
.ch-body p+p{margin-top:1em}
.draw-tag{display:inline-block;margin-top:1.2rem;font-size:.72rem;font-weight:600;
  letter-spacing:.2em;text-transform:uppercase;color:var(--olive-deep);
  border:1px solid var(--olive);border-radius:999px;padding:.45rem 1rem}
.gal{display:grid;gap:clamp(1.2rem,2.5vw,2.4rem);margin-top:.5rem}
.gal-pair{grid-template-columns:1fr}
@media(min-width:760px){.gal-pair{grid-template-columns:1fr 1fr}}
.gal-triple{grid-template-columns:1fr}
@media(min-width:760px){.gal-triple{grid-template-columns:repeat(3,1fr)}}
.gal-stack{grid-template-columns:min(100%,880px);justify-content:center}
.gal-single{grid-template-columns:1fr}
.gal-essay{grid-template-columns:min(100%,640px)}
.g-fig button{all:unset;display:block;width:100%;cursor:zoom-in}
.g-fig button:focus-visible{outline:2px solid var(--olive);outline-offset:4px}
.g-media{display:block;overflow:hidden;border-radius:2px;background:var(--ivory-2)}
.g-media img{width:100%;transition:transform 1s var(--ease)}
.g-fig button:hover .g-media img{transform:scale(1.03)}
.g-fig figcaption{margin-top:.8rem;font-size:.9rem;color:var(--mut);max-width:70ch}

.related{background:var(--ivory-2);border-top:1px solid var(--line-soft)}
.rel-grid{display:grid;grid-template-columns:1fr;gap:clamp(1.6rem,3vw,2.8rem);
  margin-top:2.6rem}
@media(min-width:760px){.rel-grid{grid-template-columns:repeat(3,1fr)}}
.rel-card{text-decoration:none;display:block}
.rel-media{overflow:hidden;border-radius:2px}
.rel-media img{width:100%;aspect-ratio:16/10;object-fit:cover;
  transition:transform 1s var(--ease)}
.rel-card:hover .rel-media img{transform:scale(1.04)}
.rel-card h3{font-size:1.45rem;margin:.9rem 0 .3rem}
.rel-card p{font-size:.9rem;color:var(--mut)}

.p-next{display:grid;grid-template-columns:1fr;text-decoration:none;
  background:var(--ink);color:var(--ivory);overflow:hidden}
@media(min-width:900px){.p-next{grid-template-columns:1.15fr 1fr}}
.p-next-media{min-height:300px;overflow:hidden}
.p-next-media img{width:100%;height:100%;object-fit:cover;min-height:300px;
  transition:transform 1.2s var(--ease)}
.p-next:hover .p-next-media img{transform:scale(1.04)}
.p-next-copy{padding:clamp(2.5rem,5vw,4.5rem);display:flex;flex-direction:column;
  justify-content:center;gap:1.2rem}
.p-next-copy .eyebrow{margin-bottom:0}
.p-next-copy h2{font-size:clamp(2rem,4.4vw,3.6rem)}
.p-next-go{display:inline-flex;align-items:center;gap:.6em;font-size:.8rem;
  font-weight:600;letter-spacing:.22em;text-transform:uppercase;color:var(--stone)}

.p-cta{background:var(--paper);text-align:center;border-top:1px solid var(--line-soft)}

/* ============================================================
   PROJECT INDEX
   ============================================================ */
.idx-head{padding-top:calc(4.5rem + 2rem);padding-bottom:2rem}
.idx-tools{display:flex;flex-direction:column;gap:1.4rem;margin-top:2.4rem}
.idx-search label{display:block;font-size:.76rem;font-weight:600;letter-spacing:.22em;
  text-transform:uppercase;color:var(--mut);margin-bottom:.7rem}
.idx-search input{
  width:100%;max-width:560px;font:inherit;font-size:1.05rem;color:var(--ink);
  background:var(--paper);border:1px solid var(--line);border-radius:999px;
  padding:.95rem 1.6rem;
}
.idx-search input::placeholder{color:#8E8978}
.idx-filters{display:flex;flex-wrap:wrap;gap:.7rem}
.chip{font:inherit;font-size:.8rem;font-weight:600;letter-spacing:.1em;
  border:1px solid var(--line);background:transparent;color:var(--mut);
  border-radius:999px;padding:.6rem 1.25rem;cursor:pointer;
  transition:all .3s var(--ease)}
.chip:hover{border-color:var(--olive);color:var(--ink)}
.chip[aria-pressed="true"]{background:var(--ink);border-color:var(--ink);color:var(--ivory)}
.idx-status{font-size:.85rem;color:var(--mut);letter-spacing:.06em}
.idx-grid{display:grid;grid-template-columns:1fr;gap:clamp(2rem,3.5vw,3rem);
  padding-bottom:clamp(4rem,7vw,6rem)}
@media(min-width:640px){.idx-grid{grid-template-columns:1fr 1fr}}
@media(min-width:1100px){.idx-grid{grid-template-columns:1fr 1fr 1fr}}
.idx-card{text-decoration:none;display:block}
.idx-card[hidden]{display:none}
.idx-media{overflow:hidden;border-radius:2px;background:var(--ivory-2)}
.idx-media img{width:100%;aspect-ratio:4/3;object-fit:cover;
  transition:transform 1s var(--ease)}
.idx-card:hover .idx-media img{transform:scale(1.04)}
.idx-card h2{font-size:1.6rem;margin:.95rem 0 .35rem}
.idx-meta{font-size:.78rem;font-weight:600;letter-spacing:.18em;
  text-transform:uppercase;color:var(--mut)}
.idx-loc{font-size:.92rem;color:var(--mut);margin-top:.25rem}
.no-results{grid-column:1/-1;text-align:center;color:var(--mut);
  font-family:var(--serif);font-size:1.5rem;padding:3rem 0}

/* ---------- responsive header/nav ---------- */
@media(max-width:860px){
  .site-nav{display:none}
  .menu-btn{display:flex}
}

/* ---------- reference homepage: intro split ---------- */
.intro-split{display:grid;grid-template-columns:1.05fr .95fr;
  gap:clamp(2.5rem,5vw,6rem);align-items:start}
.intro-statement{font-size:clamp(2.3rem,4.6vw,4.1rem);max-width:13ch}
.intro-side p{color:var(--mut);font-size:1.04rem;max-width:46ch}
.text-link{display:inline-flex;align-items:center;gap:.6em;margin-top:1.7rem;
  font-size:.76rem;font-weight:600;letter-spacing:.24em;text-transform:uppercase;
  text-decoration:none;border-bottom:1px solid currentColor;padding-bottom:.45em}
.text-link span{transition:transform .3s var(--ease)}
.text-link:hover span{transform:translateX(5px)}
.on-dark .text-link{color:var(--ivory)}

/* ---------- selected works ---------- */
.selworks{background:var(--ink);color:var(--ivory)}
.sel-title{font-size:clamp(2.4rem,5vw,4.4rem);margin-bottom:clamp(2.5rem,4vw,4rem)}
.sel-years{font-style:normal;font-size:.52em;color:var(--mut-l);letter-spacing:.08em}
.sel-grid{display:grid;grid-template-columns:repeat(4,1fr);
  gap:clamp(1rem,2vw,1.75rem)}
.sel-card{margin:0;min-width:0}
.sel-card a{display:block;text-decoration:none;color:inherit}
.sel-media{display:block;overflow:hidden;aspect-ratio:3/4;background:var(--ink-2)}
.sel-media img{width:100%;height:100%;object-fit:cover;
  transition:transform 1.2s var(--ease)}
.sel-card a:hover .sel-media img,
.sel-card a:focus-visible .sel-media img{transform:scale(1.03)}
.sel-card h3{font-size:1.32rem;line-height:1.28;margin:1.15rem 0 .45rem}
.sel-meta{font-size:.66rem;font-weight:600;letter-spacing:.2em;color:var(--mut-l)}

/* ---------- project index table ---------- */
.idxtable{padding-block:clamp(3.5rem,6vw,6rem)}
.idx-head,.idx-row{display:grid;grid-template-columns:3.5rem 1fr 8rem 9rem 5rem 2.5rem;
  gap:1rem;align-items:baseline}
.idx-head{padding:0 0 1rem;font-size:.66rem;font-weight:600;letter-spacing:.24em;
  text-transform:uppercase;color:var(--mut);border-bottom:1px solid var(--line)}
.idx-row{padding:1.15rem 0;text-decoration:none;color:inherit;
  border-bottom:1px solid var(--line-soft);
  transition:background .3s var(--ease),padding .3s var(--ease)}
.idx-row:hover{background:var(--paper);padding-left:.7rem}
.idx-num{color:var(--mut);font-size:.88rem}
.idx-proj{font-family:var(--serif);font-size:1.18rem;line-height:1.3}
.idx-type,.idx-loc,.idx-year{font-size:.92rem;color:var(--mut)}
.idx-arr{text-align:right;transition:transform .3s var(--ease)}
.idx-row:hover .idx-arr{transform:translateX(6px)}

/* ---------- in dialogue with the landscape ---------- */
.land-head{display:grid;grid-template-columns:1fr 1fr;
  gap:clamp(2rem,5vw,5rem);align-items:end;
  margin-bottom:clamp(2.5rem,4vw,4rem)}
.land-note{color:var(--mut);max-width:42ch;justify-self:end;margin:0}
.land-grid{display:grid;grid-template-columns:repeat(4,1fr);
  gap:clamp(1rem,2vw,1.6rem)}
.land-card{margin:0;min-width:0}
.land-card button{display:block;width:100%;padding:0;border:0;background:none;
  cursor:zoom-in;color:inherit}
.land-media{display:block;overflow:hidden;aspect-ratio:4/3;background:var(--ivory-2)}
.land-media img{width:100%;height:100%;object-fit:cover;
  transition:transform 1.2s var(--ease)}
.land-card button:hover .land-media img,
.land-card button:focus-visible .land-media img{transform:scale(1.04)}
.land-card figcaption{font-size:.64rem;font-weight:600;letter-spacing:.24em;
  text-transform:uppercase;color:var(--mut);padding-top:.85rem}

/* ---------- studio (dark) ---------- */
.studio-dark{background:var(--ink);color:var(--ivory)}
.studio-split{display:grid;grid-template-columns:1fr 1fr;
  gap:clamp(2.5rem,5vw,6rem);align-items:center}
.studio-media .rv-media{display:block;overflow:hidden}
.studio-media img{width:100%;height:auto}
.studio-copy .sec-title{margin-bottom:1.6rem}
.studio-copy p{color:var(--mut-l);max-width:46ch}

/* ---------- our process ---------- */
.proc-grid{display:grid;grid-template-columns:repeat(4,1fr);
  margin-top:clamp(2.5rem,4vw,4rem)}
.proc-step{padding:0 clamp(1.2rem,2vw,2.2rem);border-left:1px solid var(--line)}
.proc-step:first-child{border-left:0;padding-left:0}
.proc-num{display:block;font-family:var(--serif);font-size:1.05rem;
  color:var(--mut);margin-bottom:1.1rem}
.proc-step h3{font-size:1.55rem;margin-bottom:.75rem}
.proc-step p{font-size:.94rem;color:var(--mut);line-height:1.65}

/* ---------- publications ---------- */
.pubs-split{display:grid;grid-template-columns:1.15fr .85fr;
  gap:clamp(2.5rem,6vw,7rem);margin-top:clamp(2rem,3vw,3rem);align-items:start}
.pubs-list{list-style:none;margin:0;padding:0}
.pubs-list li{display:grid;grid-template-columns:4rem 1fr;gap:1.2rem;
  padding:1.35rem 0;border-top:1px solid var(--line-soft)}
.pubs-list li:last-child{border-bottom:1px solid var(--line-soft)}
.pub-year{font-size:.85rem;color:var(--mut)}
.pubs-list h3{font-family:var(--sans);font-size:1rem;font-weight:600;line-height:1.5}
.pubs-list p{font-size:.9rem;color:var(--mut);margin-top:.15rem}
.pub-quote{margin:0}
.pub-quote p{font-family:var(--serif);font-style:italic;
  font-size:clamp(1.45rem,2.4vw,2rem);line-height:1.42}
.pub-quote cite{display:block;margin-top:1.3rem;font-style:normal;font-size:.76rem;
  letter-spacing:.16em;text-transform:uppercase;color:var(--mut)}

/* ---------- contact band ---------- */
.contact-band{position:relative;color:var(--ivory);overflow:hidden;background:var(--ink)}
.contact-bg{position:absolute;inset:0}
.contact-bg img{width:100%;height:100%;object-fit:cover}
.contact-band::after{content:"";position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(23,26,23,.62),rgba(23,26,23,.38))}
.contact-inner{position:relative;z-index:1;
  padding-block:clamp(6rem,12vw,11rem);max-width:760px}
.contact-title{font-size:clamp(2.6rem,5.5vw,5rem);margin:1.3rem 0 1.4rem}
.contact-copy{color:rgba(242,240,233,.84);max-width:46ch;margin-bottom:2.4rem}
.btn-dark{display:inline-flex;align-items:center;gap:.7em;background:var(--ink);
  color:var(--ivory);padding:1.05rem 2rem;font-size:.78rem;font-weight:600;
  letter-spacing:.22em;text-transform:uppercase;text-decoration:none;
  transition:background .3s var(--ease),transform .3s var(--ease)}
.btn-dark:hover{background:var(--ink-3);transform:translateY(-2px)}
.btn-dark span{transition:transform .3s var(--ease)}
.btn-dark:hover span{transform:translateX(5px)}

/* ---------- footer ---------- */
.site-footer{background:var(--ink);color:var(--ivory);
  padding:clamp(3.5rem,6vw,5.5rem) 0 2.1rem}
.foot-grid{display:grid;grid-template-columns:1fr auto 1fr;gap:2rem;align-items:center;
  padding-bottom:2.6rem;border-bottom:1px solid var(--line-l-soft)}
.foot-word{font-family:var(--serif);font-size:clamp(1.7rem,2.8vw,2.4rem);
  letter-spacing:.16em;text-decoration:none;color:var(--ivory)}
.foot-mail{font-size:.95rem;color:var(--mut-l);text-decoration:none}
.foot-mail:hover{color:var(--ivory)}
.foot-social{display:flex;gap:1.9rem;justify-self:end}
.foot-social span{font-size:.76rem;font-weight:600;letter-spacing:.2em;
  text-transform:uppercase;color:var(--mut-l)}
.foot-base{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;
  padding-top:1.9rem;font-size:.78rem;color:var(--mut-l)}
.foot-base p{margin:0}

/* ---------- reference homepage: responsive ---------- */
@media(max-width:1020px){
  .sel-grid{grid-template-columns:repeat(2,1fr)}
  .land-grid{grid-template-columns:repeat(2,1fr)}
  .proc-grid{grid-template-columns:repeat(2,1fr);gap:2.2rem 0}
  .proc-step:nth-child(3){border-left:0;padding-left:0}
  .pubs-split,.studio-split,.land-head,.intro-split{grid-template-columns:1fr}
  .land-note{justify-self:start}
  .idx-head{display:none}
  .idx-row{grid-template-columns:3rem 1fr 2.2rem}
  .idx-type,.idx-loc,.idx-year{display:none}
  .foot-grid{grid-template-columns:1fr;gap:1.3rem}
  .foot-social{justify-self:start}
}
@media(max-width:600px){
  .sel-grid{grid-template-columns:1fr}
  .proc-grid{grid-template-columns:1fr}
  .proc-step{border-left:0;padding-left:0;border-top:1px solid var(--line-soft);
    padding-top:1.6rem}
  .proc-step:first-child{border-top:0;padding-top:0}
  .foot-base{flex-direction:column;gap:.4rem}
}

/* ---------- reduced motion ---------- */
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation-duration:.01ms!important;
    animation-iteration-count:1!important;transition-duration:.01ms!important}
  .js [data-rv]{opacity:1;transform:none}
  .js [data-rv="clip"] .rv-media{clip-path:none}
  .scroll-cue i::after{animation:none}
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


def hero_section(p):
    h = SITE['hero']
    fallback = ORDERED[0] if ORDERED else GROUPS['sohra-culture']
    key = h['image'] if asset(h['image']) else fallback['hero']
    g = GROUPS.get(h.get('project_id')) or fallback
    return f'''<section class="hero" aria-labelledby="home-title">
  <div class="hero-media">{img(key, h.get('alt') or g['title'], eager=True)}</div>
  <div class="hero-scrim" aria-hidden="true"></div>
  <div class="hero-inner wrap">
    <p class="hero-desc" data-rv>{e(h['descriptor'])}</p>
    <h1 id="home-title" class="hero-title" data-rv="d1">{em_last(h['headline'])}</h1>
  </div>
  <span class="scroll-cue" aria-hidden="true">Scroll<i></i></span>
</section>'''


def intro_section():
    s = SITE['intro']
    copy = e(s.get('copy') or '')
    return f'''<section class="sec intro" aria-label="Introduction">
  <div class="wrap intro-split">
    <h2 class="intro-statement" data-rv>{em_last(s['statement'])}</h2>
    <div class="intro-side" data-rv="d1">
      <p>{copy}</p>
      <a class="text-link" href="#approach">Our approach <span aria-hidden="true">&rarr;</span></a>
    </div>
  </div>
</section>'''


def work_section(p):
    cards = []
    for w in SELECTED_WORKS:
        g = GROUPS.get(w['id'])
        if g is None:
            warnings.append(f"selected work missing from content: {w['id']}")
            continue
        href = f'{p}projects/{w["id"]}/'
        cards.append(f'''<article class="sel-card" data-rv="clip">
  <a href="{href}" aria-label="{e(w['name'])} \u2014 view project">
    <span class="sel-media rv-media">{img(g['hero'], w['name'] + ' \u2014 design visualisation', p=p)}</span>
    <h3>{e(w['name'])}</h3>
    <p class="sel-meta">{e(w['meta'])}</p>
  </a>
</article>''')
    return f'''<section class="selworks sec on-dark" id="work" aria-labelledby="work-title">
  <div class="wrap">
    <h2 class="sel-title" id="work-title" data-rv>Selected works <span class="sel-years">/ 2021\u20142026</span></h2>
    <div class="sel-grid">
{chr(10).join(cards)}
    </div>
  </div>
</section>'''


def index_table_section(p):
    head = '''<div class="idx-head" aria-hidden="true">
      <span>#</span><span>Project</span><span>Type</span><span>Location</span><span>Year</span><span></span>
    </div>'''
    rows = []
    for num, name, typ, loc, year, pid in INDEX_ROWS:
        rows.append(f'''<a class="idx-row" href="{p}projects/{pid}/" data-rv
       aria-label="{e(name)} \u2014 view project">
      <span class="idx-num">{num}</span>
      <span class="idx-proj">{e(name)}</span>
      <span class="idx-type">{e(typ)}</span>
      <span class="idx-loc">{e(loc)}</span>
      <span class="idx-year">{year}</span>
      <span class="idx-arr" aria-hidden="true">&rarr;</span>
    </a>''')
    return f'''<section class="sec idxtable" aria-label="Project index">
  <div class="wrap">
{head}
{chr(10).join(rows)}
  </div>
</section>'''


def landscape_section(p):
    gal = SITE['landscape_gallery']
    headline = gal.get('headline') or 'In dialogue with the landscape.'
    intro = ('We see landscape as a living system \u2014 a cultural, ecological '
             'and social framework that shapes how we design, build and belong.')
    figs = []
    for key, cap, proj in FIELD_ITEMS:
        if asset(key) is None:
            continue
        figs.append(f'''<figure class="land-card" data-rv="clip">
  <button data-lb-item data-lb-group="land" data-full="{p}assets/{key}.webp"
          data-cap="{e(cap)} \u2014 {e(proj)}" data-alt="{e(cap)} \u2014 {e(proj)}"
          aria-label="Enlarge: {e(cap)}">
    <span class="land-media rv-media">{img(key, cap + ' \u2014 ' + proj, p=p)}</span>
  </button>
  <figcaption>{e(cap)}</figcaption>
</figure>''')
    return f'''<section class="sec landscape" id="landscape" aria-labelledby="land-title">
  <div class="wrap">
    <div class="land-head">
      <h2 class="sec-title" id="land-title" data-rv>{em_last(headline)}</h2>
      <p class="land-note" data-rv="d1">{e(intro)}</p>
    </div>
    <div class="land-grid" data-lb-group="land">
{chr(10).join(figs)}
    </div>
  </div>
</section>'''


def studio_section(p):
    s = SITE['studio']
    media = ''
    if s.get('image') and asset(s['image']):
        media = (f'<div class="studio-media" data-rv="clip">'
                 f'<div class="rv-media">{img(s["image"], s.get("image_alt") or "Studio", p=p)}</div>'
                 f'</div>')
    return f'''<section class="studio-dark sec on-dark" id="studio" aria-labelledby="studio-title">
  <div class="wrap studio-split">
    {media}
    <div class="studio-copy">
      <h2 class="sec-title" id="studio-title" data-rv>{em_last(s['headline'])}</h2>
      <p data-rv="d1">{e(s.get('intro') or '')}</p>
      <a class="text-link" data-rv="d2" href="{p}project-index/">About the studio <span aria-hidden="true">&rarr;</span></a>
    </div>
  </div>
</section>'''


def approach_section():
    a = SITE['approach']
    stages = '\n'.join(
        f'''<div class="proc-step" data-rv>
        <span class="proc-num">{e(st['n'])}</span>
        <h3>{e(st['title'])}</h3>
        <p>{e(st['text'])}</p>
      </div>''' for st in a['stages'])
    return f'''<section class="sec process" id="approach" aria-labelledby="approach-title">
  <div class="wrap">
    <p class="eyebrow" data-rv>Our process</p>
    <div class="proc-grid">
{stages}
    </div>
  </div>
</section>'''


def publications_section():
    lis = []
    for year, outlet, project, note in PUBLICATIONS:
        title = f'{outlet} \u2014 {project}' if project else outlet
        lis.append(f'''<li data-rv>
        <span class="pub-year">{e(year)}</span>
        <div><h3>{e(title)}</h3><p>{e(note)}</p></div>
      </li>''')
    quote, cite = PUB_QUOTE
    return f'''<section class="sec pubs" aria-labelledby="pubs-title">
  <div class="wrap">
    <p class="eyebrow" data-rv>Selected publications &amp; recognition</p>
    <div class="pubs-split">
      <ul class="pubs-list" id="pubs-title">
{chr(10).join(lis)}
      </ul>
      <blockquote class="pub-quote" data-rv="d1">
        <p>{e(quote)}</p>
        <cite>\u2014 {e(cite)}</cite>
      </blockquote>
    </div>
  </div>
</section>'''


def journal_section():
    entries = journal_published()
    if not entries:
        return ''
    lis = []
    for j in entries:
        link = ''
        if j.get('url'):
            link = (f'<a class="j-ext" href="{e(j["url"])}" target="_blank" '
                    f'rel="noopener">Read {arrow()}</a>')
        lis.append(f'''<li data-rv>
        <span class="j-date">{e(j.get('date', ''))}</span>
        <div><h3 class="j-title">{e(j.get('title', ''))}</h3>
        <p class="j-sum">{e(j.get('summary', ''))}</p></div>
        {link}
      </li>''')
    return f'''<section class="sec" id="journal" aria-labelledby="journal-title">
  <div class="wrap">
    <p class="eyebrow" data-rv>Journal</p>
    <h2 class="sec-title" id="journal-title" data-rv>Notes &amp; <em>news</em></h2>
    <ul class="journal-list">
{chr(10).join(lis)}
    </ul>
  </div>
</section>'''


def contact_section(p):
    c = SITE['contact']
    email = c.get('email') or ''
    bg = ''
    if c.get('image') and asset(c['image']):
        bg = (f'<div class="contact-bg" aria-hidden="true">'
              f'{img(c["image"], "", p=p)}</div>')
    cta = (f'<a class="btn-dark" data-rv="d2" href="mailto:{e(email)}">'
           f'Discuss a project <span aria-hidden="true">&rarr;</span></a>' if email else '')
    return f'''<section class="contact-band" id="contact" aria-labelledby="contact-title">
  {bg}
  <div class="wrap contact-inner">
    <p class="eyebrow light" data-rv>Get in touch</p>
    <h2 class="contact-title" id="contact-title" data-rv>{em_last(c['headline'])}</h2>
    <p class="contact-copy" data-rv="d1">{e(c.get('copy') or '')}</p>
    {cta}
  </div>
</section>'''


SECTION_BUILDERS = {
    'hero': lambda p: hero_section(p),
    'intro': lambda p: intro_section(),
    'work': lambda p: work_section(p),
    'index_table': lambda p: index_table_section(p),
    'landscape': lambda p: landscape_section(p),
    'studio': lambda p: studio_section(p),
    'approach': lambda p: approach_section(),
    'publications': lambda p: publications_section(),
    'journal': lambda p: journal_section(),
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


def chapter_section(s, n, p):
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
    return f'''<section class="chapter" id="{e(s.get('anchor') or f'chapter-{n}')}"
         aria-labelledby="ch-title-{n}">
  <div class="wrap">
    <div class="ch-head">
      <span class="ch-num" data-rv>{str(n).zfill(2)}</span>
      <div>
        <h2 data-rv id="ch-title-{n}">{e(s['title'])}</h2>
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
        cta = (f'<a class="btn" data-rv href="mailto:{e(c["email"])}">'
               f'Get in touch {arrow()}</a>')
    return f'''<section class="p-cta sec">
  <div class="wrap">
    <p class="eyebrow" data-rv style="justify-content:center">Contact</p>
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

    chapters = '\n'.join(chapter_section(s, n_, p)
                         for n_, s in enumerate(g['slides'], 1))
    rel_cards = '\n'.join(
        f'''<a class="rel-card" data-rv href="{p}projects/{r['id']}/">
      <span class="rel-media">{img(r['hero'], r['title'] + ' — design visualisation', p=p)}</span>
      <h3>{e(r['title'])}</h3>
      <p>{e(r['location'])}</p>
    </a>''' for r in rel)

    body = f'''<div class="p-top wrap">
  <a href="{p}project-index/">← Project index</a>
  <span>N° {number} — {e(g['category'])}</span>
</div>
<section class="p-hero" aria-label="{e(g['title'])} — hero image">
  {img(g['hero'], g['title'] + ' — design visualisation', eager=True, p=p)}
</section>
<section class="p-head">
  <div class="wrap">
    <p class="p-loc" data-rv>{e(g['location'])}</p>
    <h1 class="p-title" data-rv="d1">{e(g['title'])}</h1>
    <p class="p-lede" data-rv="d2">{e(g['body'].strip())}</p>
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
    <p class="eyebrow" data-rv>Related</p>
    <h2 class="sec-title" data-rv>Continue <em>exploring</em></h2>
    <div class="rel-grid">
{rel_cards}
    </div>
  </div>
</section>
<a class="p-next on-dark" href="{p}projects/{next_g['id']}/" data-rv="clip">
  <span class="p-next-media rv-media">{img(next_g['hero'], next_g['title'] + ' — design visualisation', p=p)}</span>
  <span class="p-next-copy">
    <span class="eyebrow light">Next project — {str(next_g['number']).zfill(2)}</span>
    <h2>{e(next_g['title'])}</h2>
    <span class="p-next-go">View project {arrow()}</span>
  </span>
</a>
{cta_band(p)}'''
    desc = g['body'].strip()[:300]
    return shell(f"{g['title']} — Ola Magdy", desc, body,
                 p=p, page='project-page', og_image=g['hero'])


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
