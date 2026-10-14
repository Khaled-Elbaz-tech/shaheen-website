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

def shell(title, body, desc, home=False, p='', page=''):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title><meta name="description" content="{e(desc.strip())}"><meta name="theme-color" content="#141615"><link rel="icon" href="{p}favicon.svg" type="image/svg+xml"><script>document.documentElement.className+=' js'</script><link rel="stylesheet" href="{p}style.css?v=6"><script src="{p}site.js?v=5" defer></script></head>
<body class="{page}"><a class="skip" href="#main">Skip to content</a>
<div class="loader" id="loader" aria-hidden="true"><div class="loader-inner"><span class="loader-word">ola magdy<em>.</em></span><span class="loader-line"><span></span></span></div></div>
<div class="progress" aria-hidden="true"><span id="progressBar"></span></div>
<header class="site-header"><a class="wordmark" href="{p}" aria-label="Ola Magdy home">ola magdy<span class="brand-dot">.</span></a><nav aria-label="Main navigation"><a class="nav-link" href="{p}#work">Work <sup>01</sup></a><a class="nav-link" href="{p}#about">About <sup>02</sup></a><a class="nav-link nav-cta" href="{p}project-index/">Index {arrow()}</a></nav></header>
<main id="main">{body}</main>
<footer class="site-footer"><div class="foot-top" data-rv><p class="eyebrow light">Ola Magdy \u2014 Architecture</p><a class="foot-word" href="{p}" aria-label="Back to home">Ola Magdy</a></div><div class="foot-meta"><p>Principal Associate Designer \u00b7 Archohm</p><p>Project credit: Archohm. Design proposals &amp; studies.</p><a class="to-top" href="#main">Back to top \u2191</a></div></footer>
</body></html>'''

# ---------------------------------------------------------------- homepage

hero = f'''<section class="hero" aria-labelledby="home-title">
<div class="hero-media" data-parallax="0.28">{img('d34s027i0','A sheltered colonnade framing water and the domed pavilion at the Sohra Culture and Experience Centre',True)}</div>
<div class="hero-grain" aria-hidden="true"></div>
<div class="hero-shade" aria-hidden="true"></div>
<div class="hero-content">
<p class="eyebrow light" data-rv>Ola Magdy \u2014 Selected architecture</p>
<h1 id="home-title" class="hero-title"><span class="lm"><span>Spaces that</span></span><span class="lm"><span>move <em>us.</em></span></span></h1>
<div class="hero-foot"><p class="hero-sub" data-rv>Architecture, landscape<br>&amp; the life in between.</p><a class="btn-film" href="#work" data-magnetic><span>Discover the work</span></a></div>
</div>
<a class="hero-cap" href="projects/sohra-culture/"><span><b>01</b> Sohra Culture &amp; Experience Centre</span><span>Meghalaya, India {arrow()}</span></a>
<span class="scroll-cue" aria-hidden="true">Scroll<span></span></span>
</section>'''

marquee = '''<div class="marquee" aria-hidden="true"><div class="marquee-track"><span>Architecture</span><i>\u00b7</i><span>Landscape</span><i>\u00b7</i><span>Urbanism</span><i>\u00b7</i><span>Architecture</span><i>\u00b7</i><span>Landscape</span><i>\u00b7</i><span>Urbanism</span><i>\u00b7</i></div></div>'''

intro = '''<section class="intro section"><div class="intro-inner">
<p class="eyebrow" data-rv>The practice \u2014 A personal perspective</p>
<h2 class="intro-state" data-rv>Thinking across scales.<br>Designing <em>with place.</em></h2>
<div class="intro-copy" data-rv><p>Ola Magdy is an architect and Principal Associate Designer at Archohm, with professional experience in Egypt and India. Her work spans architecture, landscape, urban design and masterplanning \u2014 from cultural buildings and healthcare campuses to public spaces and city-scale proposals.</p><a class="text-link" href="#about">More about Ola {arrow()}</a></div>
<div class="disc-line" data-rv><span>Architecture</span><span>Landscape</span><span>Urban design</span><span>Masterplanning</span></div>
</div></section>'''

def film_card(g, n):
    return f'''<article class="film-card"><a class="film-link" href="projects/{g['id']}/" aria-label="{e(g['title'])} \u2014 view project">
<div class="film-media" data-parallax="0.12">{img(g['hero'],g['title']+' \u2014 architectural design visualisation')}</div>
<div class="film-shade" aria-hidden="true"></div>
<div class="film-meta"><span class="film-num">{str(n).zfill(2)}</span><span>{e(g['category'])}</span><span>{e(g['location'])}</span></div>
<h3 class="film-title"><span class="lm"><span>{e(g['title'])}</span></span></h3>
<span class="film-view">View project {arrow()}</span>
</a></article>'''

selected_ids = ['sohra-culture','palliative-care','umiam-lake','mandalgre','sohra-cement','farmers-market']
featured = '<section id="work" class="featured"><div class="sec-head section" data-rv><p class="eyebrow light">01 \u2014 Featured</p><h2 class="mega light">Selected<br><em>work</em></h2><p class="sec-note">Places for gathering. Spaces for living.</p></div><div class="film-stack">'
for gid in selected_ids:
    g = GROUPS[gid]
    featured += film_card(g, g['number'])
featured += '</div></section>'

interlude = f'''<section class="interlude"><div class="inter-media" data-parallax="0.18">{img('d34s034i0','Sohra Culture and Experience Centre \u2014 aerial design visualisation at dusk')}</div>
<div class="inter-shade" aria-hidden="true"></div>
<div class="inter-inner"><p class="eyebrow light" data-rv>Architecture in its landscape</p><a class="inter-quote" data-rv href="projects/sohra-culture/">A cultural landscape,<br><em>shaped by rain.</em> {arrow()}</a><p class="inter-sub" data-rv>Sohra, Meghalaya \u2014 Design study</p></div></section>'''

archive = '<section class="archive section"><div class="sec-head" data-rv><p class="eyebrow">02 \u2014 Archive</p><h2 class="mega">Further<br><em>explorations</em></h2><a class="text-link" href="project-index/">Explore the full project index {arrow()}</a></div><div class="work-list">'
for g in C['groups']:
    if g['id'] in selected_ids or g.get('collection'): continue
    archive += f'''<a class="work-row" data-rv href="projects/{g['id']}/"><span class="work-num">{str(g['number']).zfill(2)}</span><span class="work-main"><span class="work-title">{e(g['title'])}</span><span class="work-sub">{e(g['location'])}</span></span><span class="work-cat">{e(g['category'])}</span><span class="work-thumb">{img(g['hero'],g['title'])}</span><span class="work-arrow" aria-hidden="true">\u2197</span></a>'''
archive += '</div></section>'

studies = '<section class="studies section"><div class="sec-head" data-rv><p class="eyebrow">03 \u2014 Field studies</p><h2 class="mega">In dialogue<br>with the <em>landscape.</em></h2><p class="sec-note">Conservation, craft, culture and hospitality in the hills of Meghalaya.</p></div><div class="studies-grid">'
for g in C['groups']:
    if not g.get('collection'): continue
    studies += f'''<a class="study-card" data-rv href="projects/{g['id']}/"><div class="study-media">{img(g['hero'],g['title']+' \u2014 site and design study')}</div><div class="study-body"><h3>{e(g['title'])} {arrow()}</h3><p>{e(g['category'])}</p></div></a>'''
studies += '</div></section>'

about = f'''<section class="about" id="about"><div class="section">
<div class="sec-head" data-rv><p class="eyebrow light">04 \u2014 About Ola</p></div>
<div class="about-grid">
<div class="about-media" data-rv><div class="portrait-frame">{img('d34s032i0','Gallery interior study for the Sohra Culture and Experience Centre')}</div><p class="caption light">Sohra Culture &amp; Experience Centre \u2014 Gallery study</p></div>
<div class="about-copy">
<h2 class="about-name" data-rv>Ola Magdy<span>Architect. Designer.<br><em>Educator.</em></span></h2>
<p class="about-role" data-rv>Principal Associate Designer<br><span>Archohm \u00b7 India</span></p>
<p class="about-lead" data-rv>A practice shaped by two countries, different disciplines, and the movement between buildings, landscapes and cities.</p>
</div></div>
<div class="bio-grid">
<p class="eyebrow light" data-rv>Practice across<br>Egypt &amp; India</p>
<div class="bio-copy" data-rv><p class="bio-lede">Ola Magdy is an architect, designer and educator whose career spans professional practice in Egypt and India. Since 2016, she has progressed from a junior architectural role to senior practice, university teaching and her current position as Principal Associate Designer at Archohm.</p><p>Her early career in Egypt included Bonyan Designs, Ebtekarak and Eiffel. In India, her experience expanded through a Visiting Professor appointment at the World University of Design, followed by Senior Architect roles at Srishti Architects and Creative Group. She joined Archohm in 2024.</p><p>At Archohm, her portfolio extends from cultural and civic buildings to healthcare, housing, hospitality and public landscapes. The work presented here includes proposals across Meghalaya, Bihar and Bodoland, where individual buildings sit within wider questions of terrain, movement, community and urban growth.</p></div>
</div>
<div class="career">
<div class="career-head" data-rv><p class="eyebrow light">Professional experience</p><h3>A journey through<br><em>practice &amp; teaching.</em></h3></div>
<ol class="timeline">
<li data-rv><span class="tl-years">2024 \u2014 Present</span><div class="tl-main"><h4>Archohm</h4><p>Principal Associate Designer</p></div><span class="tl-place">India</span></li>
<li data-rv><span class="tl-years">2023</span><div class="tl-main"><h4>Creative Group</h4><p>Senior Architect</p></div><span class="tl-place">India</span></li>
<li data-rv><span class="tl-years">2022 \u2014 2023</span><div class="tl-main"><h4>Srishti Architects</h4><p>Senior Architect</p></div><span class="tl-place">India</span></li>
<li data-rv><span class="tl-years">2021 \u2014 2022</span><div class="tl-main"><h4>World University of Design</h4><p>Visiting Professor</p></div><span class="tl-place">India</span></li>
<li data-rv><span class="tl-years">2018 \u2014 2020</span><div class="tl-main"><h4>Eiffel</h4><p>Architect</p></div><span class="tl-place">Egypt</span></li>
<li data-rv><span class="tl-years">2017 \u2014 2018</span><div class="tl-main"><h4>Ebtekarak</h4><p>Architect</p></div><span class="tl-place">Egypt</span></li>
<li data-rv><span class="tl-years">2016 \u2014 2017</span><div class="tl-main"><h4>Bonyan Designs</h4><p>Junior Architect</p></div><span class="tl-place">Egypt</span></li>
</ol></div>
<div class="process-grid">
<div class="process-copy"><p class="eyebrow light" data-rv>A way of working</p><h3 data-rv>From observation<br>to <em>architecture.</em></h3><div data-rv><p>Physical models, drawings and visual studies help Ola explore how an idea becomes a place. Site visits and conversations with project stakeholders bring the realities of landscape, use and context into that process.</p><p>Her interest in architecture extends to experiencing buildings firsthand: observing how daylight enters a room, how materials meet and how people move through a space.</p></div><a class="text-link light" data-rv href="project-index/">Explore the work {arrow()}</a></div>
</div>
<div class="about-credit" data-rv><span>Practice &amp; collaboration</span><p>The projects in this portfolio were developed at Archohm. Ola\u2019s wider career is documented above; project credit remains with the originating practice.</p></div>
</div></section>'''

philosophy = '''<section class="philo"><div class="philo-inner section">
<p class="eyebrow light" data-rv>05 \u2014 Philosophy</p>
<h2 class="philo-state" data-rv>Thinking across scales.<br>Designing <em>with place.</em></h2>
<div class="philo-items">
<div class="philo-item" data-rv><span>01</span><h3>Place first</h3><p>Every project begins with the study of site \u2014 its light, its materials, and the people who will inhabit it.</p></div>
<div class="philo-item" data-rv><span>02</span><h3>Making as thinking</h3><p>Physical model-making remains central to the process: ideas tested by hand before they are drawn.</p></div>
<div class="philo-item" data-rv><span>03</span><h3>The everyday</h3><p>Architecture measured not by image, but by the daily life it quietly holds.</p></div>
</div></div></section>'''

contact = '''<section class="contact section"><div class="contact-inner" data-rv>
<p class="eyebrow">06 \u2014 Contact</p>
<h2 class="mega">Let\u2019s start a<br><em>conversation.</em></h2>
<p class="contact-copy">Ola is available for select commissions and collaborations across architecture, landscape and urban design.</p>
<a class="cta-big" href="project-index/" data-magnetic><span>Explore the work</span><i aria-hidden="true">\u2197</i></a>
</div></section>'''

(D/'index.html').write_text(shell('Ola Magdy \u2014 Architecture, Landscape & Urbanism',hero+marquee+intro+featured+interlude+archive+studies+about+philosophy+contact,'Ola Magdy, Principal Associate Designer at Archohm. A portfolio of architecture, cultural spaces, landscapes and urban design.',True,page='home'),encoding='utf-8')
print('Homepage updated')

# ---------------------------------------------------------------- project pages

for gi, g in enumerate(C['groups']):
    title = e(g['title'])
    number = str(g['number']).zfill(2)
    rel_ids = [C['groups'][(gi+k) % len(C['groups'])]['id'] for k in (1,2,3)]
    # Collect all slide images for the study explorer
    all_imgs = []
    for s in g['slides']:
        caps = [s['captions']] if isinstance(s['captions'], str) else s['captions']
        if len(caps) != len(s['images']): raise ValueError('Caption count mismatch in '+g['id'])
        for k, cap in zip(s['images'], caps):
            all_imgs.append((k, cap, s['title']))
    cats = []
    for k, cap, st in all_imgs:
        if st not in cats: cats.append(st)
    body = f'''<section class="p-film">
<div class="p-film-media" data-parallax="0.22">{img(g['hero'],g['title']+' \u2014 design study',True,p='../../')}</div>
<div class="hero-grain" aria-hidden="true"></div>
<div class="p-film-shade" aria-hidden="true"></div>
<div class="p-film-top"><a href="../../project-index/">\u2190 Index</a><span>N\u00b0 {number} \u2014 {e(g['category'])}</span></div>
<div class="p-film-title">
<p class="eyebrow light" data-rv>{e(g['location'])}</p>
<h1><span class="lm"><span>{title}</span></span></h1>
<dl class="p-meta" data-rv>
<div><dt>Location</dt><dd>{e(g['location'])}</dd></div>
<div><dt>Category</dt><dd>{e(g['category'])}</dd></div>
<div><dt>Design role</dt><dd>Ola Magdy, Principal Associate Designer</dd></div>
<div><dt>Practice</dt><dd>Archohm</dd></div>
</dl></div>
<span class="scroll-cue" aria-hidden="true">Scroll<span></span></span>
</section>
<section class="p-overview section"><p class="eyebrow" data-rv>Overview</p><p class="p-lede" data-rv>{e(g['body'].strip())}</p></section>'''
    if len(all_imgs) > 1:
        body += '<section class="explorer"><div class="exp-inner section"><div class="exp-head" data-rv><p class="eyebrow light">Visual study</p><h2 class="exp-title">The project<br><em>in drawings.</em></h2></div>'
        body += '<div class="exp-filters" data-rv role="group" aria-label="Filter studies"><button data-exp-filter="All" aria-pressed="true">All</button>'
        for c in cats:
            body += f'<button data-exp-filter="{e(c)}" aria-pressed="false">{e(c)}</button>'
        body += '</div>'
        k0, cap0, _ = all_imgs[0]
        body += f'''<div class="exp-stage" data-rv><a class="exp-main enlarge-image" href="../../assets/{k0}.webp" aria-label="Enlarge: {e(cap0)}">{img(k0,cap0,p='../../')}</a><span class="exp-count" data-exp-count>01 / {str(len(all_imgs)).zfill(2)}</span></div>
<div class="exp-caprow" data-rv><p data-exp-caption>{e(cap0)}</p></div>
<div class="exp-thumbs" data-rv>'''
        for i, (k, cap, st) in enumerate(all_imgs):
            body += f'''<button data-exp-src="../../assets/{k}.webp" data-exp-cap="{e(cap)}" data-exp-cat="{e(st)}" aria-pressed="{'true' if i==0 else 'false'}" aria-label="View: {e(cap)}">{img(k,cap,p='../../')}<span>{str(i+1).zfill(2)}</span></button>'''
        body += '</div></div></section>'
    if len(g['slides']) > 1:
        body += '<nav class="chapter-nav" aria-label="In this project"><div class="section"><p class="eyebrow" data-rv>Chapters</p><ol>'
        for n, s in enumerate(g['slides'], 1):
            body += f'<li data-rv><a href="#chapter-{n}"><span>{n:02}</span>{e(s["title"])}</a></li>'
        body += '</ol></div></nav>'
    for n, s in enumerate(g['slides']):
        captions = [s['captions']] if isinstance(s['captions'], str) else s['captions']
        body += f'''<section class="chapter section" id="chapter-{n+1}"><div class="ch-head"><span class="ch-num" data-rv>{str(n+1).zfill(2)}</span><div><h2 data-rv>{e(s['title'])}</h2><p data-rv>{e(s['body']).replace(chr(10),'<br>')}</p></div></div><div class="gal images-{len(s['images'])}">'''
        for k, cap in zip(s['images'], captions):
            ratio = A[k]['width'] / A[k]['height']
            body += f'''<figure class="g-fig {'pano' if ratio>2.3 else ''}" data-rv><a class="enlarge-image" href="../../assets/{k}.webp" target="_blank" rel="noopener" aria-label="Enlarge: {e(cap)}"><span class="g-media">{img(k,cap,p='../../')}</span><span class="g-zoom" aria-hidden="true">\u2197</span></a><figcaption>{e(cap)}</figcaption></figure>'''
        body += '</div></section>'
    body += '<section class="related section"><div class="sec-head" data-rv><p class="eyebrow">Related</p><h2 class="mega">Continue<br><em>exploring</em></h2></div><div class="rel-grid">'
    for rid in rel_ids:
        rg = GROUPS[rid]
        body += f'''<a class="rel-card" data-rv href="../../projects/{rg['id']}/"><div class="rel-media">{img(rg['hero'],rg['title'],p='../../')}</div><div class="rel-info"><span>{str(rg['number']).zfill(2)}</span><div><h3>{e(rg['title'])}</h3><p>{e(rg['location'])}</p></div></div></a>'''
    body += '</div></section>'
    nxt = C['groups'][(gi+1) % len(C['groups'])]
    body += f'''<a class="p-next" href="../../projects/{nxt['id']}/"><div class="p-next-media" data-parallax="0.15">{img(nxt['hero'],nxt['title']+' \u2014 design visualisation',p='../../')}</div><div class="p-next-shade" aria-hidden="true"></div><div class="p-next-copy"><p class="eyebrow light" data-rv>Next project \u2014 {str(nxt['number']).zfill(2)}</p><h2 data-rv>{e(nxt['title'])}</h2><span class="p-next-arrow" aria-hidden="true">\u2197</span></div></a>
<dialog class="viewer" aria-label="Enlarged project image"><div class="viewer-tools"><button data-viewer="prev">\u2190 Prev</button><button data-viewer="next">Next \u2192</button><button data-viewer="zin">Zoom +</button><button data-viewer="zout">Zoom \u2212</button><button data-viewer="reset">Reset</button></div><button class="viewer-close" aria-label="Close enlarged image">Close \u00d7</button><figure><img src="../../assets/{g['hero']}.webp" alt=""><figcaption></figcaption></figure><a class="viewer-original" href="../../assets/{g['hero']}.webp" target="_blank" rel="noopener">Open original \u2197</a></dialog>'''
    out = D/'projects'/g['id']; out.mkdir(parents=True, exist_ok=True)
    (out/'index.html').write_text(shell(g['title']+' \u2014 Ola Magdy', body, g['body'], p='../../', page='project-page'), encoding='utf-8')
print(f'Updated {len(C["groups"])} project pages')

# ---------------------------------------------------------------- project index

indexbody = '<section class="idx-hero section"><p class="eyebrow" data-rv>The complete portfolio</p><h1 class="mega" data-rv>Projects, places<br>&amp; <em>possibilities.</em></h1><div class="idx-search" data-rv><label for="project-search">Find a project or place</label><input id="project-search" type="search" placeholder="Try Umiam, market or healthcare\u2026" autocomplete="off"><p class="search-status" role="status" aria-live="polite"></p></div></section><div class="cat-grid section">'
for r in REGISTER:
    indexbody += f'''<article class="cat-card" data-rv data-cat-entry data-search="{e(r['title'])} {e(r['location'])} {e(r['category'])}"><a href="../projects/{r['id']}/"><div class="cat-media">{img(r['hero'],r['title']+' \u2014 design study',p='../')}<span class="cat-arrow" aria-hidden="true">\u2197</span></div><div class="cat-body"><p class="cat-meta">{e(r['category'])}</p><h2>{e(r['title'])}</h2><p class="cat-loc">{e(r['location'])}</p></div></a></article>'''
indexbody += '<p class="no-results" hidden>No matching projects. Try a different name, programme or place.</p></div>'
out = D/'project-index'; out.mkdir(exist_ok=True)
(out/'index.html').write_text(shell('Project Index \u2014 Ola Magdy', indexbody, 'Explore Ola Magdy\u2019s architecture, landscape and urban design portfolio at Archohm, including individual programmes within larger masterplans.', p='../', page='idx-page'), encoding='utf-8')
print('Full project index updated')
