from pathlib import Path
import json, html

ROOT = Path(__file__).parent
D = ROOT / 'dist'
C = json.loads((ROOT / 'content.json').read_text(encoding='utf-8'))
A = json.loads((ROOT / 'assets.json').read_text(encoding='utf-8'))
REGISTER = json.loads((ROOT / 'project-register.json').read_text(encoding='utf-8'))
e = html.escape
GROUPS = {g['id']: g for g in C['groups']}

def img(key, alt, eager=False, cls=''):
    a = A[key]
    return f'<img src="/assets/{key}.webp" width="{a["width"]}" height="{a["height"]}" alt="{e(alt)}" class="{cls}" loading="{"eager" if eager else "lazy"}" decoding="async" {"fetchpriority=high" if eager else ""}>'

def arrow():
    return '<span aria-hidden="true">↗</span>'

def shell(title, body, desc, home=False):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title><meta name="description" content="{e(desc.strip())}"><meta name="theme-color" content="#161817"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/style.css?v=3"><script src="/site.js?v=2" defer></script></head>
<body class="{'home' if home else 'project-page'}"><a class="skip" href="#main">Skip to content</a>
<header class="site-header"><a class="wordmark" href="/" aria-label="Ola Magdy home">ola magdy<span class="brand-period">.</span></a><span class="header-discipline">Architecture &amp; urbanism</span><nav aria-label="Main navigation"><a href="/#work">Work <span>01</span></a><a href="/#profile">About <span>02</span></a><a class="nav-index" href="/project-index/">Project index {arrow()}</a></nav></header>
<main id="main">{body}</main>
<footer class="site-footer"><div class="footer-top"><span class="eyebrow">Ola Magdy / Architecture</span><a href="/#profile">About Ola {arrow()}</a></div><a class="footer-name" href="/">Ola Magdy</a><div class="footer-bottom"><p>Principal Associate Designer · Archohm</p><p>Project credit: Archohm. Design proposals &amp; studies.</p><a href="#main">Back to top ↑</a></div></footer>
</body></html>'''

def project_card(g, n, cls=''):
    return f'''<article class="project-card {cls} reveal"><a href="/projects/{g['id']}/"><div class="card-image">{img(g['hero'],g['title']+' — architectural design visualisation')}<span class="image-link">View project {arrow()}</span></div><div class="card-meta"><span>{str(n).zfill(2)} / {e(g['category'])}</span><span>{e(g['location'])}</span></div><h3>{e(g['title'])}</h3></a></article>'''

hero = f'''<section class="home-hero" aria-labelledby="home-title"><div class="hero-image">{img('d34s027i0','A sheltered colonnade framing water and the domed pavilion at the Sohra Culture and Experience Centre',True)}</div><div class="hero-shade"></div><div class="hero-content"><p class="eyebrow">Selected architecture &amp; spatial explorations</p><h1 id="home-title">Ola Magdy</h1><div class="hero-bottom"><p>Between architecture,<br>landscape &amp; everyday life.</p><a class="circle-link" href="#work" aria-label="Explore the projects"><span>Explore<br>the work</span><b aria-hidden="true">↓</b></a></div></div><a class="hero-caption" href="/projects/sohra-culture/"><span>Sohra Culture &amp; Experience Centre</span><span>Meghalaya, India {arrow()}</span></a></section>'''

intro = '''<section class="intro-section section-pad"><p class="eyebrow">The practice / A personal perspective</p><div class="intro-layout"><h2>Thinking across scales.<br>Designing <em>with place.</em></h2><div class="intro-copy"><p>Ola Magdy is an architect and Principal Associate Designer at Archohm, with professional experience in Egypt and India. Her work spans architecture, landscape, urban design and masterplanning, from cultural buildings and healthcare campuses to public spaces and city-scale proposals.</p><a class="text-link" href="#profile">More about Ola <span aria-hidden="true">↗</span></a></div></div><div class="discipline-line"><span>Architecture</span><span>Landscape</span><span>Urban design</span><span>Masterplanning</span></div></section>'''

selected_ids = ['sohra-culture','palliative-care','umiam-lake','mandalgre','sohra-cement','farmers-market']
selected = '<section id="work" class="selected-work section-pad"><div class="section-title"><div><p class="eyebrow">01 / The portfolio</p><h2>Selected <em>work</em></h2></div><p>Places for gathering.<br>Spaces for living.</p></div><div class="selected-grid">'
for n, gid in enumerate(selected_ids):
    selected += project_card(GROUPS[gid],GROUPS[gid]['number'],f'card-{n+1}')
selected += '</div></section>'

interlude = f'''<section class="image-interlude"><div>{img('d34s034i0','Sohra Culture and Experience Centre — aerial design visualisation at dusk')}</div><div class="interlude-caption"><p class="eyebrow">Architecture in its landscape</p><a href="/projects/sohra-culture/">A cultural landscape,<br><em>shaped by rain.</em> {arrow()}</a><p>Sohra, Meghalaya / Design study</p></div></section>'''

archive = '<section class="project-index section-pad" id="all-projects"><div class="section-title"><div><p class="eyebrow">Further explorations</p><h2>Across the <em>scales</em></h2></div><a class="text-link" href="/project-index/">Explore the full project index <span aria-hidden="true">↗</span></a></div><div class="index-list">'
for g in C['groups']:
    if g['id'] in selected_ids or g.get('collection'): continue
    archive += f'''<a class="index-row" href="/projects/{g['id']}/"><span class="index-number">{str(g['number']).zfill(2)}</span><div class="index-image">{img(g['hero'],g['title']+' — design study')}</div><div class="index-title"><h3>{e(g['title'])}</h3><p>{e(g['location'])}</p></div><span class="index-category">{e(g['category'])}</span><span class="index-arrow" aria-hidden="true">↗</span></a>'''
archive += '</div></section>'

regional = '<section class="regional-section section-pad"><div class="section-title"><div><p class="eyebrow">Meghalaya / Regional proposals</p><h2>In dialogue with<br>the <em>landscape.</em></h2></div><p>Conservation, craft, culture and hospitality in the hills of Meghalaya.</p></div><div class="regional-grid">'
for g in C['groups']:
    if not g.get('collection'): continue
    regional += f'<a href="/projects/{g["id"]}/"><div>{img(g["hero"],g["title"]+" — site and design study")}</div><h3>{e(g["title"])} {arrow()}</h3><p>{e(g["category"])}</p></a>'
regional += '</div><a class="text-link" href="/project-index/">All projects, programmes &amp; studies <span aria-hidden="true">↗</span></a></section>'

profile = f'''<section class="profile-section section-pad" id="profile"><p class="eyebrow">02 / About Ola</p><div class="profile-heading"><h2>Curiosity.<br>Craft.<br><em>Connection.</em></h2><div class="profile-figure">{img('d34s032i0','Gallery interior study for the Sohra Culture and Experience Centre')}<p>Sohra Culture &amp; Experience Centre / Gallery study</p></div></div><div class="profile-body"><p class="profile-role">Ola Magdy<br><span>Principal Associate Designer<br>Archohm</span></p><div><p class="profile-lead">Ola Magdy is an architect working across buildings, landscapes and cities. Her approach brings together the study of place, physical making and the everyday experience of architecture.</p><p>As Principal Associate Designer at Archohm, she works across cultural, healthcare, residential and public-realm projects. Her professional experience spans Egypt and India, and this portfolio documents her work in Meghalaya, Bihar and Bodoland.</p><p>Physical model-making remains a valued part of her design process. Site visits, conversations with project stakeholders and the study of buildings through travel continue to shape her understanding of space, light, materials and the people who inhabit them.</p><p>From a small intervention beside a river to a wider vision for a city, this collection follows the work from early studies to architectural drawings and visualisations.</p></div></div><div class="profile-credit"><span>Practice &amp; collaboration</span><p>Projects shown were developed at Archohm. Individual pages document design proposals, development studies and alternative schemes.</p></div></section>'''

(D/'index.html').write_text(shell('Ola Magdy — Architecture, Landscape & Urbanism',hero+intro+selected+interlude+archive+regional+profile,'Ola Magdy, Principal Associate Designer at Archohm. A portfolio of architecture, cultural spaces, landscapes and urban design.',True),encoding='utf-8')
print('Homepage updated')

for gi, g in enumerate(C['groups']):
    title = e(g['title'])
    number = str(g['number']).zfill(2)
    body = f'''<section class="project-opening section-pad"><div class="project-breadcrumb"><a href="/project-index/">← Project index</a><span>Collection {number}</span></div><p class="eyebrow">{e(g['category'])} / {e(g['location'])}</p><h1>{title}</h1><div class="project-summary"><p>{e(g['body'].strip())}</p><dl><div><dt>Design role</dt><dd>Ola Magdy<br>Principal Associate Designer</dd></div><div><dt>Practice</dt><dd>Archohm</dd></div><div><dt>Portfolio material</dt><dd>{'Regional study' if g['id']=='bodoland-study' else 'Design proposals &amp; studies'}</dd></div></dl></div></section><figure class="project-cover">{img(g['hero'],g['title']+' — design study',True)}<figcaption><span>{title}</span><span>{e(g['location'])}</span></figcaption></figure>'''
    if len(g['slides'])>1:
        body += '<nav class="chapter-nav" aria-label="In this collection"><p class="eyebrow">In this collection</p><ol>'
        for n,p in enumerate(g['slides'],1):
            body += f'<li><a href="#chapter-{n}"><span>{n:02}</span>{e(p["title"])}</a></li>'
        body += '</ol></nav>'
    body += '<div class="project-chapters">'
    for n, p in enumerate(g['slides']):
        captions = [p['captions']] if isinstance(p['captions'],str) else p['captions']
        if len(captions)!=len(p['images']): raise ValueError('Caption count mismatch')
        body += f'''<section class="project-chapter section-pad" id="chapter-{n+1}"><div class="chapter-heading"><span class="chapter-number">{str(n+1).zfill(2)}</span><h2>{e(p['title'])}</h2><p>{e(p['body']).replace(chr(10),'<br>')}</p></div><div class="project-gallery images-{len(p['images'])} layout-{p['layout']}">'''
        for k, cap in zip(p['images'], captions):
            ratio = A[k]['width'] / A[k]['height']
            body += f'''<figure class="gallery-figure {'panorama' if ratio>2.3 else ''}"><a class="enlarge-image" href="/assets/{k}.webp" target="_blank" rel="noopener" aria-label="Enlarge: {e(cap)}">{img(k,cap)}<span class="enlarge-icon" aria-hidden="true">↗</span></a><figcaption>{e(cap)}</figcaption></figure>'''
        body += '</div></section>'
    nxt = C['groups'][(gi+1)%len(C['groups'])]
    body += f'''</div><div class="project-end-credit"><span>Ola Magdy / Archohm</span><p>The drawings and visualisations document design proposals, development studies and alternative schemes. Project credit: Archohm.</p></div><a class="next-project" href="/projects/{nxt['id']}/"><div class="next-image">{img(nxt['hero'],nxt['title']+' — design visualisation')}</div><div class="next-copy"><p class="eyebrow">Continue exploring / {str(nxt['number']).zfill(2)}</p><h2>{e(nxt['title'])}</h2><span class="next-arrow" aria-hidden="true">↗</span></div></a><dialog class="image-viewer" aria-label="Enlarged project image"><button class="viewer-close" aria-label="Close enlarged image">Close ×</button><figure><img src="/assets/{g['hero']}.webp" alt=""><figcaption></figcaption></figure><a class="viewer-original" href="/assets/{g['hero']}.webp" target="_blank" rel="noopener">Open original image ↗</a></dialog>'''
    out=D/'projects'/g['id'];out.mkdir(parents=True,exist_ok=True)
    (out/'index.html').write_text(shell(g['title']+' — Ola Magdy',body,g['body']),encoding='utf-8')
print(f'Updated {len(C["groups"])} project pages')

indexbody = '<section class="register-opening section-pad"><p class="eyebrow">The complete portfolio / Archohm</p><h1>Projects, places<br>&amp; <em>possibilities.</em></h1><div class="register-intro"><p>Explore the buildings, landscapes and urban studies within each collection. Larger masterplans bring together several programmes, each linked below to its drawings and design studies.</p><label for="project-search">Find a project or place<input id="project-search" type="search" placeholder="Try Umiam, market or healthcare…" autocomplete="off"></label></div><p class="search-status" role="status" aria-live="polite"></p></section><div class="register-list">'
for n,r in enumerate(REGISTER,1):
    indexbody += f'<section class="register-group" data-project-group><div class="register-heading"><p class="eyebrow">{n:02} / {e(r["category"])}</p><a href="/projects/{r["id"]}/"><h2>{e(r["title"])} {arrow()}</h2></a><p>{e(r["location"])}</p></div><div class="register-entries">'
    for entry in r['entries']:
        indexbody += f'<a href="{entry["href"]}">{e(entry["title"])}<span aria-hidden="true">↗</span></a>'
    indexbody += '</div></section>'
indexbody += '<p class="register-empty" hidden>No matching projects. Try a different name, programme or place.</p></div>'
out=D/'project-index';out.mkdir(exist_ok=True)
(out/'index.html').write_text(shell('Project Index — Ola Magdy',indexbody,'Explore Ola Magdy’s architecture, landscape and urban design portfolio at Archohm, including individual programmes within larger masterplans.'),encoding='utf-8')
print('Full project index updated')
