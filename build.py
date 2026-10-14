from pathlib import Path
import json, html

ROOT = Path(__file__).parent
D = ROOT / 'dist'
C = json.loads((ROOT / 'content.json').read_text(encoding='utf-8'))
A = json.loads((ROOT / 'assets.json').read_text(encoding='utf-8'))
REGISTER = json.loads((ROOT / 'project-register.json').read_text(encoding='utf-8'))
e = html.escape
GROUPS = {g['id']: g for g in C['groups']}

def img(key, alt, eager=False, cls='', p=''):
    a = A[key]
    return f'<img src="{p}assets/{key}.webp" width="{a["width"]}" height="{a["height"]}" alt="{e(alt)}" class="{cls}" loading="{"eager" if eager else "lazy"}" decoding="async" {"fetchpriority=high" if eager else ""}>'

def arrow():
    return '<span aria-hidden="true">\u2197</span>'

def shell(title, body, desc, home=False, p=''):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title><meta name="description" content="{e(desc.strip())}"><meta name="theme-color" content="#0a0a0a"><link rel="icon" href="{p}favicon.svg" type="image/svg+xml"><script>document.documentElement.className+=' js'</script><link rel="stylesheet" href="{p}style.css?v=5"><script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js" defer></script><script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js" defer></script><script src="{p}site.js?v=4" defer></script></head>
<body class="{'home' if home else 'project-page'}"><a class="skip" href="#main">Skip to content</a>
<div class="loader" id="loader" aria-hidden="true"><div class="loader-inner"><span class="loader-word">ola magdy<em>.</em></span><span class="loader-bar"><span></span></span></div></div>
<div class="scroll-progress" aria-hidden="true"><span id="progressBar"></span></div>
<header class="site-header"><a class="wordmark" href="{p}" aria-label="Ola Magdy home">ola magdy<span class="brand-period">.</span></a><nav aria-label="Main navigation"><a class="nav-link" href="{p}#work">Work <sup>01</sup></a><a class="nav-link" href="{p}#about">About <sup>02</sup></a><a class="nav-link nav-index" href="{p}project-index/">Index {arrow()}</a></nav></header>
<main id="main">{body}</main>
<footer class="site-footer"><div class="footer-cta" data-reveal><p class="eyebrow">Ola Magdy / Architecture</p><a class="footer-name" href="{p}">Ola Magdy</a></div><div class="footer-meta"><p>Principal Associate Designer \u00b7 Archohm</p><p>Project credit: Archohm. Design proposals &amp; studies.</p><a class="to-top" href="#main">Back to top \u2191</a></div></footer>
</body></html>'''

# ---------------------------------------------------------------- homepage

hero = f'''<section class="hero" aria-labelledby="home-title">
<div class="hero-media" data-parallax="0.25">{img('d34s027i0','A sheltered colonnade framing water and the domed pavilion at the Sohra Culture and Experience Centre',True)}</div>
<div class="hero-scrim"></div>
<div class="hero-content">
<p class="eyebrow" data-reveal>Architecture \u00b7 Landscape \u00b7 Urbanism</p>
<h1 id="home-title" class="hero-title"><span class="lm"><span>Ola</span></span><span class="lm"><span>Magdy<em>.</em></span></span></h1>
<div class="hero-foot"><p class="hero-sub" data-reveal>Designing spaces that shape<br>human experience.</p><a class="hero-scroll" href="#work" aria-label="Scroll to selected work"><span>Scroll</span><i>\u2193</i></a></div>
</div>
<a class="hero-caption" href="projects/sohra-culture/"><span>Sohra Culture &amp; Experience Centre</span><span>Meghalaya, India {arrow()}</span></a>
</section>'''

def feat_card(g, n, cls):
    return f'''<article class="feat-card {cls}" data-reveal><a href="projects/{g['id']}/"><div class="feat-media">{img(g['hero'],g['title']+' \u2014 architectural design visualisation')}<span class="feat-view">View {arrow()}</span></div><div class="feat-info"><span class="feat-num">{str(n).zfill(2)}</span><div><h3>{e(g['title'])}</h3><p>{e(g['category'])} \u00b7 {e(g['location'])}</p></div></div></a></article>'''

selected_ids = ['sohra-culture','palliative-care','umiam-lake','mandalgre','sohra-cement','farmers-market']
feat_classes = ['f1','f2','f3','f4','f5','f6']
featured = '<section id="work" class="featured section"><div class="section-head" data-reveal><p class="eyebrow">01 \u2014 Featured</p><h2 class="mega">Selected<br><em>work</em></h2></div><div class="featured-grid">'
for cls, gid in zip(feat_classes, selected_ids):
    g = GROUPS[gid]
    featured += feat_card(g, g['number'], cls)
featured += '</div></section>'

works = '<section class="works section"><div class="section-head" data-reveal><p class="eyebrow">02 \u2014 Archive</p><h2 class="mega">Further<br><em>explorations</em></h2><a class="text-link" href="project-index/">Full project index {arrow()}</a></div><div class="work-list">'
for g in C['groups']:
    if g['id'] in selected_ids or g.get('collection'): continue
    works += f'''<a class="work-row" data-reveal href="projects/{g['id']}/"><span class="work-num">{str(g['number']).zfill(2)}</span><span class="work-title">{e(g['title'])}</span><span class="work-loc">{e(g['location'])}</span><span class="work-cat">{e(g['category'])}</span><span class="work-thumb">{img(g['hero'],g['title'])}</span><span class="work-arrow" aria-hidden="true">\u2197</span></a>'''
works += '</div></section>'

studies = '<section class="studies section"><div class="section-head" data-reveal><p class="eyebrow">03 \u2014 Field studies</p><h2 class="mega">Regional<br><em>proposals</em></h2><p class="section-note">Conservation, craft, culture and hospitality in the hills of Meghalaya.</p></div><div class="studies-grid">'
for g in C['groups']:
    if not g.get('collection'): continue
    studies += f'''<a class="study-card" data-reveal href="projects/{g['id']}/"><div class="study-media">{img(g['hero'],g['title']+' \u2014 site and design study')}</div><h3>{e(g['title'])} {arrow()}</h3><p>{e(g['category'])}</p></a>'''
studies += '</div></section>'

about = f'''<section class="about section" id="about"><div class="section-head" data-reveal><p class="eyebrow">04 \u2014 About</p></div>
<div class="about-grid">
<div class="about-portrait" data-reveal><div class="portrait-frame" data-parallax="0.12">{img('d34s032i0','Gallery interior study for the Sohra Culture and Experience Centre')}</div><p class="caption">Sohra Culture &amp; Experience Centre / Gallery study</p></div>
<div class="about-copy">
<p class="about-role" data-reveal>Ola Magdy<br><span>Principal Associate Designer, Archohm</span></p>
<blockquote class="about-quote" data-reveal>\u201cBetween architecture,<br>landscape &amp; <em>everyday life.</em>\u201d</blockquote>
<div class="about-bio" data-reveal><p>Ola Magdy is an architect working across buildings, landscapes and cities. Her approach brings together the study of place, physical making and the everyday experience of architecture.</p><p>As Principal Associate Designer at Archohm, she works across cultural, healthcare, residential and public-realm projects. Her professional experience spans Egypt and India, and this portfolio documents her work in Meghalaya, Bihar and Bodoland.</p><p>Physical model-making remains a valued part of her design process. Site visits, conversations with project stakeholders and the study of buildings through travel continue to shape her understanding of space, light, materials and the people who inhabit them.</p></div>
</div></div></section>'''

philosophy = '''<section class="philosophy section"><div class="philo-inner">
<p class="eyebrow" data-reveal>05 \u2014 Philosophy</p>
<h2 class="philo-statement" data-reveal>Thinking across scales.<br>Designing <em>with place.</em></h2>
<div class="philo-grid">
<div class="philo-item" data-reveal><span>01</span><h3>Place first</h3><p>Every project begins with the study of site \u2014 its light, its materials, and the people who will inhabit it.</p></div>
<div class="philo-item" data-reveal><span>02</span><h3>Making as thinking</h3><p>Physical model-making remains central to the process: ideas tested by hand before they are drawn.</p></div>
<div class="philo-item" data-reveal><span>03</span><h3>The everyday</h3><p>Architecture measured not by image, but by the daily life it quietly holds.</p></div>
</div></div></section>'''

experience = '''<section class="experience section"><div class="section-head" data-reveal><p class="eyebrow">06 \u2014 Experience</p><h2 class="mega">Practice &amp;<br><em>research</em></h2></div>
<div class="timeline">
<div class="tl-item" data-reveal><div class="tl-role"><h3>Principal Associate Designer</h3><p>Archohm</p></div><p class="tl-focus">Cultural \u00b7 Healthcare \u00b7 Residential \u00b7 Public realm</p></div>
<div class="tl-item" data-reveal><div class="tl-role"><h3>Professional practice</h3><p>Egypt &amp; India</p></div><p class="tl-focus">Architecture \u00b7 Landscape \u00b7 Urban design \u00b7 Masterplanning</p></div>
<div class="tl-item" data-reveal><div class="tl-role"><h3>Field research</h3><p>Meghalaya \u00b7 Bihar \u00b7 Bodoland</p></div><p class="tl-focus">Site studies \u00b7 Stakeholder dialogue \u00b7 Model-making</p></div>
</div></section>'''

contact = f'''<section class="contact section"><div class="contact-inner" data-reveal>
<p class="eyebrow">07 \u2014 Contact</p>
<h2 class="mega">Let\u2019s start a<br><em>conversation.</em></h2>
<p class="contact-copy">Ola is available for select commissions and collaborations across architecture, landscape and urban design.</p>
<a class="cta-link" href="project-index/" data-magnetic><span>Explore the work</span><i>\u2197</i></a>
</div></section>'''

(D/'index.html').write_text(shell('Ola Magdy \u2014 Architecture, Landscape & Urbanism',hero+featured+works+studies+about+philosophy+experience+contact,'Ola Magdy, Principal Associate Designer at Archohm. A portfolio of architecture, cultural spaces, landscapes and urban design.',True),encoding='utf-8')
print('Homepage updated')

# ---------------------------------------------------------------- project pages

for gi, g in enumerate(C['groups']):
    title = e(g['title'])
    number = str(g['number']).zfill(2)
    rel_ids = [C['groups'][(gi+k) % len(C['groups'])]['id'] for k in (1,2,3)]
    body = f'''<section class="p-hero">
<div class="p-hero-media" data-parallax="0.22">{img(g['hero'],g['title']+' \u2014 design study',True,p='../../')}</div>
<div class="p-hero-scrim"></div>
<div class="p-hero-content">
<div class="p-crumb" data-reveal><a href="../../project-index/">\u2190 Index</a><span>N\u00b0 {number}</span></div>
<p class="eyebrow" data-reveal>{e(g['category'])} \u2014 {e(g['location'])}</p>
<h1 class="p-title"><span class="lm"><span>{title}</span></span></h1>
<dl class="p-meta" data-reveal>
<div><dt>Location</dt><dd>{e(g['location'])}</dd></div>
<div><dt>Category</dt><dd>{e(g['category'])}</dd></div>
<div><dt>Design role</dt><dd>Ola Magdy, Principal Associate Designer</dd></div>
<div><dt>Practice</dt><dd>Archohm</dd></div>
</dl></div></section>
<section class="p-overview section"><p class="eyebrow" data-reveal>Overview</p><p class="p-lede" data-reveal>{e(g['body'].strip())}</p></section>'''
    if len(g['slides']) > 1:
        body += '<nav class="chapter-nav section" aria-label="In this project"><p class="eyebrow" data-reveal>Chapters</p><ol>'
        for n, p in enumerate(g['slides'], 1):
            body += f'<li data-reveal><a href="#chapter-{n}"><span>{n:02}</span>{e(p["title"])}</a></li>'
        body += '</ol></nav>'
    for n, p in enumerate(g['slides']):
        captions = [p['captions']] if isinstance(p['captions'], str) else p['captions']
        if len(captions) != len(p['images']): raise ValueError('Caption count mismatch')
        body += f'''<section class="p-chapter section" id="chapter-{n+1}"><div class="chapter-head"><span class="chapter-num" data-reveal>{str(n+1).zfill(2)}</span><div><h2 data-reveal>{e(p['title'])}</h2><p data-reveal>{e(p['body']).replace(chr(10),'<br>')}</p></div></div><div class="p-gallery images-{len(p['images'])} layout-{p['layout']}">'''
        for k, cap in zip(p['images'], captions):
            ratio = A[k]['width'] / A[k]['height']
            body += f'''<figure class="g-fig {'pano' if ratio>2.3 else ''}" data-reveal><a class="enlarge-image" href="../../assets/{k}.webp" target="_blank" rel="noopener" aria-label="Enlarge: {e(cap)}"><span class="g-media">{img(k,cap,p='../../')}</span><span class="g-zoom" aria-hidden="true">\u2197</span></a><figcaption>{e(cap)}</figcaption></figure>'''
        body += '</div></section>'
    body += '<section class="p-related section"><div class="section-head" data-reveal><p class="eyebrow">Related</p><h2 class="mega">Continue<br><em>exploring</em></h2></div><div class="related-grid">'
    for rid in rel_ids:
        rg = GROUPS[rid]
        body += f'''<a class="rel-card" data-reveal href="../../projects/{rg['id']}/"><div class="rel-media">{img(rg['hero'],rg['title'],p='../../')}</div><div class="rel-info"><span>{str(rg['number']).zfill(2)}</span><h3>{e(rg['title'])}</h3><p>{e(rg['location'])}</p></div></a>'''
    body += '</div></section>'
    nxt = C['groups'][(gi+1) % len(C['groups'])]
    body += f'''<a class="p-next" href="../../projects/{nxt['id']}/"><div class="p-next-media">{img(nxt['hero'],nxt['title']+' \u2014 design visualisation',p='../../')}</div><div class="p-next-scrim"></div><div class="p-next-copy" data-reveal><p class="eyebrow">Next project \u2014 {str(nxt['number']).zfill(2)}</p><h2>{e(nxt['title'])}</h2><span class="p-next-arrow" aria-hidden="true">\u2197</span></div></a>
<dialog class="image-viewer" aria-label="Enlarged project image"><button class="viewer-close" aria-label="Close enlarged image">Close \u00d7</button><figure><img src="../../assets/{g['hero']}.webp" alt=""><figcaption></figcaption></figure><a class="viewer-original" href="../../assets/{g['hero']}.webp" target="_blank" rel="noopener">Open original image \u2197</a></dialog>'''
    out = D/'projects'/g['id']; out.mkdir(parents=True, exist_ok=True)
    (out/'index.html').write_text(shell(g['title']+' \u2014 Ola Magdy', body, g['body'], p='../../'), encoding='utf-8')
print(f'Updated {len(C["groups"])} project pages')

# ---------------------------------------------------------------- project index

indexbody = '<section class="idx-hero section"><p class="eyebrow" data-reveal>The complete portfolio</p><h1 class="mega" data-reveal>Projects, places<br>&amp; <em>possibilities.</em></h1><div class="idx-search" data-reveal><label for="project-search">Find a project or place</label><input id="project-search" type="search" placeholder="Try Umiam, market or healthcare\u2026" autocomplete="off"><p class="search-status" role="status" aria-live="polite"></p></div></section><div class="register-list">'
for n, r in enumerate(REGISTER, 1):
    indexbody += f'<section class="register-group" data-project-group data-reveal><div class="register-heading"><p class="eyebrow">{n:02} \u2014 {e(r["category"])}</p><a href="../projects/{r["id"]}/"><h2>{e(r["title"])} {arrow()}</h2></a><p>{e(r["location"])}</p></div><div class="register-entries">'
    for entry in r['entries']:
        _href = entry["href"]
        if _href.startswith('/'): _href = '../' + _href[1:]
        indexbody += f'<a href="{_href}">{e(entry["title"])}<span aria-hidden="true">\u2197</span></a>'
    indexbody += '</div></section>'
indexbody += '<p class="register-empty" hidden>No matching projects. Try a different name, programme or place.</p></div>'
out = D/'project-index'; out.mkdir(exist_ok=True)
(out/'index.html').write_text(shell('Project Index \u2014 Ola Magdy', indexbody, 'Explore Ola Magdy\u2019s architecture, landscape and urban design portfolio at Archohm, including individual programmes within larger masterplans.', p='../'), encoding='utf-8')
print('Full project index updated')
