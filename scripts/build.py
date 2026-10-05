"""Build the static portfolio from site.json and projects.json.

Every generated link is relative, so the pages work at a GitHub Pages root
(<user>.github.io) or under a repository subpath. The one exception is
404.html: GitHub serves it from any missing path, so it uses site.json's
basePath instead.
"""
import json
import shutil
import subprocess
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
site = json.loads((ROOT / 'site.json').read_text())
projects = json.loads((ROOT / 'projects.json').read_text())
# Collections: several smaller projects presented together on one page (e.g. EdTech).
_groups_file = ROOT / 'groups.json'
collections = json.loads(_groups_file.read_text()) if _groups_file.exists() else []
YEAR = date.today().year
PORTRAIT = 'assets/ray-portrait-noir.jpg'
PORTRAIT_LIGHT = 'assets/ray-portrait-light.webp'  # transparent cutout, see scripts/portrait-cutout.swift
BASE_URL = site['url'].rstrip('/') + '/' + site.get('basePath', '/').strip('/')
BASE_URL = BASE_URL.rstrip('/') + '/'


def e(x):
    return escape(str(x), quote=True)


# --- Icons --------------------------------------------------------------------
ICONS = {
    'home': '<path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-7h6v7"/>',
    'about': '<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
    'services': '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    'work': '<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V3h8v4M3 12h18M10 12v3h4v-3"/>',
    'contact': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>',
    'cloud': '<path d="M6 19a5 5 0 1 1 0-10 7 7 0 0 1 13-1 5.5 5.5 0 0 1-1 11Z"/>',
    'code': '<path d="m8 5-6 7 6 7m8-14 6 7-6 7m-3-16-2 18"/>',
    'flow': '<rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="15" width="6" height="6" rx="1"/><path d="M9 6h7a2 2 0 0 1 2 2v7M15 12l3 3 3-3M6 9v9h6"/>',
    'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    'moon': '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/>',
    'expand': '<path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>',
}

# Runs in <head> before first paint so the saved or system theme applies without a flash.
THEME_BOOT = ("<script>(function(){var d=document.documentElement,t;d.classList.add('js');"
              "try{t=localStorage.getItem('theme')}catch(e){}"
              "if(t!=='light'&&t!=='dark')t=matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';"
              "d.dataset.theme=t})()</script>")
GITHUB_PATH = ('M12 .5C5.65.5.5 5.65.5 12a11.5 11.5 0 0 0 7.86 10.92c.58.1.79-.25.79-.56v-2c-3.2.7-3.88-1.37-3.88-1.37'
               '-.52-1.33-1.28-1.69-1.28-1.69-1.04-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.36.96'
               '.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.68 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0'
               ' .97-.31 3.17 1.18a11 11 0 0 1 5.77 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83'
               ' 1.19 3.09 0 4.41-2.7 5.38-5.26 5.67.41.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12'
               'C23.5 5.65 18.35.5 12 .5Z')


def icon(key, cls=''):
    c = f' class="{cls}"' if cls else ''
    if key == 'github':
        return f'<svg{c} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="{GITHUB_PATH}"/></svg>'
    return (f'<svg{c} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + ICONS[key] + '</svg>')


def brand_mark(gid):
    """Monogram matching the favicon. `gid` keeps gradient ids unique per page."""
    return (f'<svg class="brand-mark" viewBox="0 0 64 64" aria-hidden="true"><defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="#2d1f4a"/><stop offset="1" stop-color="#110e21"/></linearGradient></defs>'
            f'<rect x="1" y="1" width="62" height="62" rx="17" fill="url(#{gid})" stroke="#ffffff26"/>'
            '<path d="M18 46V19h9v5c3-5 7-6 12-5v9c-8-2-12 1-12 7v11z" fill="#fff"/>'
            '<circle cx="45" cy="42" r="6" fill="#ff655e"/></svg>')


def arrow():
    return '<span class="arrow" aria-hidden="true">↗</span>'


def button(text, url, secondary=False, external=False):
    cls = 'button secondary' if secondary else 'button'
    ext = ' target="_blank" rel="noopener noreferrer"' if external else ''
    return f'<a class="{cls}" href="{e(url)}"{ext}>{text} {arrow()}</a>'


# --- Images -------------------------------------------------------------------
CWEBP = shutil.which('cwebp')


def webp_for(src):
    """Return the path of a WebP copy of a PNG/JPEG screenshot, or None.

    When cwebp is installed (locally), the copy is (re)generated whenever the
    original is newer. In CI, where cwebp is absent, the committed copy is used.
    Settings keep small UI text sharp while cutting roughly 75% of the size."""
    path = ROOT / src
    if path.suffix.lower() not in ('.png', '.jpg', '.jpeg'):
        return None
    out = path.with_suffix('.webp')
    if CWEBP and path.exists() and (not out.exists() or out.stat().st_mtime < path.stat().st_mtime):
        subprocess.run([CWEBP, '-quiet', '-q', '90', '-sharp_yuv', '-m', '6', str(path), '-o', str(out)], check=True)
        print(f'Optimised {src} -> {out.name} ({path.stat().st_size // 1024} KB -> {out.stat().st_size // 1024} KB)')
    return str(Path(src).with_suffix('.webp')) if out.exists() else None


def picture(prefix, src, alt, attrs=''):
    """<picture> that serves WebP where available, with the original as fallback."""
    img = f'<img src="{prefix}{e(src)}" alt="{e(alt)}" {attrs}>'
    webp = webp_for(src)
    if not webp:
        return img
    return f'<picture><source srcset="{prefix}{e(webp)}" type="image/webp">{img}</picture>'


def tags(items):
    if not items:
        return ''
    return '<ul class="tags" aria-label="Tags">' + ''.join(f'<li>{e(t)}</li>' for t in items) + '</ul>'


# --- Page chrome --------------------------------------------------------------
NAV = [('Home', '', 'home'), ('About', 'about/', 'about'), ('Services', 'services/', 'services'),
       ('Projects', 'work/', 'work'), ('Contact', 'contact/', 'contact')]


def head(title, key, prefix, path, description=None, full_title=False):
    page_title = title if full_title else f'{title} — {site["name"]}'
    desc = description or site['intro']
    nav = ''.join(
        f'<a href="{prefix}{slug or "index.html"}"' + (' aria-current="page"' if ico == key else '') +
        f'>{icon(ico)}<span>{label}</span></a>' for label, slug, ico in NAV)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(page_title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#0e0c1d">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(site['name'])}">
<meta property="og:title" content="{e(page_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(BASE_URL + path)}">
<meta property="og:image" content="{e(BASE_URL + PORTRAIT)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600&family=Manrope:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="{prefix}assets/style.css">
{THEME_BOOT}
<script src="{prefix}assets/site.js" defer></script>
</head>
<body class="page-{key}">
<a class="skip" href="#main">Skip to content</a>
<div class="ambient" aria-hidden="true"><span></span><span></span><span></span></div>
<header class="site-header" data-header>
  <div class="header-inner">
    <a class="brand" href="{prefix}index.html" aria-label="{e(site['name'])}, home">{brand_mark('bm-head')}<span class="brand-text"><strong>{e(site['name'])}<span class="dot">.</span></strong><small>{e(site['tagline'])}</small></span></a>
    <p class="status"><span class="pulse" aria-hidden="true"></span>{e(site['status'])}</p>
    <div class="header-actions">
      <button class="icon-btn theme-toggle" type="button" data-theme-toggle aria-label="Switch to light theme">{icon('sun', 'icon-sun')}{icon('moon', 'icon-moon')}</button>
      <a class="icon-btn" href="{e(site['github'])}" target="_blank" rel="noopener noreferrer" aria-label="GitHub profile (opens in a new tab)">{icon('github')}</a>
      <a class="icon-btn" href="mailto:{e(site['email'])}" aria-label="Email {e(site['name'])}">{icon('contact')}</a>
      <a class="button button-sm" href="{prefix}contact/">Let’s talk {arrow()}</a>
    </div>
  </div>
</header>
<nav class="dock" aria-label="Main navigation">{nav}</nav>
<div class="site-shell">
'''


def footer(prefix):
    links = ''.join(f'<a href="{prefix}{slug or "index.html"}">{label}</a>' for label, slug, _ in NAV)
    return f'''<footer class="site-footer">
  <div class="footer-top">
    <div class="footer-brand"><a class="brand" href="{prefix}index.html" aria-label="{e(site['name'])}, home">{brand_mark('bm-foot')}<span class="brand-text"><strong>{e(site['name'])}<span class="dot">.</span></strong><small>{e(site['tagline'])}</small></span></a><p>Ideas. Applications. Possibilities.</p></div>
    <nav class="footer-nav" aria-label="Footer">{links}</nav>
    <div class="footer-social">
      <a class="icon-btn" href="{e(site['github'])}" target="_blank" rel="noopener noreferrer" aria-label="GitHub profile (opens in a new tab)">{icon('github')}</a>
      <a class="icon-btn" href="mailto:{e(site['email'])}" aria-label="Email {e(site['name'])}">{icon('contact')}</a>
    </div>
  </div>
  <div class="footer-bottom"><span>© {YEAR} {e(site['name'])}</span><span>Hand-built static site on GitHub Pages.</span></div>
</footer>
</div>
</body>
</html>
'''


# --- Reusable sections --------------------------------------------------------
def window_bar(p):
    if not p.get('windowBar', True):
        return ''
    return '<div class="window-bar" aria-hidden="true"><i></i><i></i><i></i></div>'


def cover_of(p):
    """Return (image, is_screenshot) for a project's card cover, or (None, False) if it has none.
    A dedicated `cover` wins; otherwise the first screenshot, then the `art` illustration."""
    if p.get('cover'):
        return p['cover'], False
    if p['screenshots']:
        return p['screenshots'][0], True
    if p.get('art'):
        return p['art'], False
    return None, False


def work_cta(prefix):
    """Compact animated pill in the hero that links to the projects page."""
    count = sum(1 for p in projects if cover_of(p)[0]) + sum(len(c['projects']) for c in collections)
    label = f'{count} project' + ('' if count == 1 else 's')
    return (f'<a class="work-cta" href="{prefix}work/">'
            f'<span class="work-cta-label"><small>{label}</small>See my work</span>'
            f'<span class="work-cta-arrow" aria-hidden="true"><i>→</i><i>→</i></span></a>')


def portrait(prefix, variant='hero'):
    badge = work_cta(prefix) if variant == 'hero' else ''
    chips = ''.join(f'<span class="chip chip-{i}" aria-hidden="true">{icon(k)}{label}</span>'
                    for i, (k, label) in enumerate([('cloud', 'Cloud'), ('code', 'Apps'), ('flow', 'Automation')]))
    return (f'<div class="portrait portrait-{variant}"><div class="rings" aria-hidden="true"><span></span><span></span></div>'
            # One portrait per theme; CSS hides the other. Lazy loading means the hidden one isn't downloaded.
            f'<img class="portrait-dark" src="{prefix}{PORTRAIT}" alt="AI-generated portrait of Ray Ali standing with his arms crossed" width="1024" height="1536" loading="lazy" fetchpriority="high">'
            f'<img class="portrait-light" src="{prefix}{PORTRAIT_LIGHT}" alt="AI-generated portrait of Ray Ali standing with his arms crossed" width="1024" height="1536" loading="lazy" fetchpriority="high">'
            f'{chips}{badge}</div>')


def cards(prefix=''):
    """Projects with a cover become full-width features that alternate sides;
    placeholders sit two per row, and a lone final placeholder spans the row."""
    html = ''
    featured_count = 0
    upcoming = [p for p in projects if not cover_of(p)[0]]
    for p in projects:
        img, is_shot = cover_of(p)
        live = img is not None
        extra = ''
        if live:
            featured_count += 1
            extra = ' reverse' if featured_count % 2 == 0 else ''
        elif len(upcoming) % 2 and p is upcoming[-1]:
            extra = ' wide'
        if is_shot:
            cover = (f'<div class="window">{window_bar(p)}'
                     + picture(prefix, img['src'], img['alt'], 'loading="lazy"') + '</div>')
        elif live:
            cover = f'<img class="art" src="{prefix}{e(img["src"])}" alt="{e(img["alt"])}" loading="lazy">'
        else:
            cover = f'<div class="placeholder-cover" aria-hidden="true"><span>{e(p["number"])}</span></div>'
        html += (f'<a class="project-card reveal {"featured" if live else "upcoming"}{extra}" href="{prefix}projects/{e(p["slug"])}/">'
                 f'<div class="card-cover">{cover}</div><div class="card-copy">'
                 f'<p class="card-meta"><span>{e(p["category"])}</span><span class="pill">{e(p["visibility"])}</span></p>'
                 f'<h3>{e(p["title"])}</h3><p class="card-summary">{e(p["summary"])}</p>{tags(p.get("tags"))}'
                 f'<span class="card-action">{"Explore project" if live else "Preview space"} {arrow()}</span></div></a>')
    for c in collections:
        html += collection_card(prefix, c)
    return '<div class="project-grid">' + html + '</div>'


def collection_card(prefix, c):
    """Full-width card for a collection, listing its projects instead of a cover image."""
    members = ''.join(f'<li><span class="member-num">{i + 1:02d}</span><strong>{e(m["title"])}</strong>'
                      f'<span>{e(m["tagline"])}</span></li>' for i, m in enumerate(c['projects']))
    n = len(c['projects'])
    return (f'<a class="project-card collection-card reveal" href="{prefix}projects/{e(c["slug"])}/"><div class="card-copy">'
            f'<p class="card-meta"><span>{e(c["category"])}</span><span class="pill">{n} project{"s" if n != 1 else ""}</span>'
            f'<span class="pill">{e(c["visibility"])}</span></p>'
            f'<h3>{e(c["title"])}</h3><p class="card-summary">{e(c["summary"])}</p>'
            f'<ul class="collection-members">{members}</ul>'
            f'<span class="card-action">Explore the collection {arrow()}</span></div></a>')


def services(prefix='', level='h2'):
    return '<div class="services-grid">' + ''.join(
        f'<article class="service-card reveal"><div class="service-top"><span class="service-icon">{icon(s["icon"])}</span><span class="service-num">0{i + 1}</span></div>'
        f'<{level}>{e(s["title"])}</{level}><p>{e(s["description"])}</p>'
        f'<a class="text-link" href="{prefix}contact/?service={e(s["icon"])}">Let’s discuss it {arrow()}</a></article>'
        for i, s in enumerate(site['services'])) + '</div>'


def cta(prefix):
    return (f'<section class="cta-band reveal"><div><p class="eyebrow">Let’s build something</p>'
            f'<h2>Got an idea worth <em>building?</em></h2>'
            f'<p>Tell me what you have in mind. Cloud, applications, automation, or something in between.</p></div>'
            f'<div class="actions">{button("Start a conversation", prefix + "contact/")}'
            f'{button("Email me", "mailto:" + site["email"], True)}</div></section>')


# --- Tech stack ---------------------------------------------------------------
TECH = site.get('tech', {})


def tech_chip(name):
    """A technology as a brand-coloured monogram tile plus its name."""
    if name not in TECH:
        raise SystemExit(f'Unknown technology "{name}": add it to "tech" in site.json')
    mono, color = TECH[name][:2]
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    ink = '#10101a' if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else '#ffffff'  # readable monogram on any brand colour
    return (f'<li class="tech" style="--c:{e(color)};--on:{ink}"><span class="tech-mark" aria-hidden="true">{e(mono)}</span>'
            f'<span class="tech-name">{e(name)}</span></li>')


def stack_section(p):
    """Project page: the stack drawn as connected layers, top (what you see) to bottom (how it ships)."""
    layers = p.get('stack') or []
    if not layers:
        return ''
    rows = ''.join(
        f'<li class="stack-layer reveal"><div class="stack-label"><span class="stack-num">{i + 1:02d}</span>'
        f'<div><h3>{e(layer["layer"])}</h3><p>{e(layer.get("note", ""))}</p></div></div>'
        f'<ul class="tech-list" aria-label="{e(layer["layer"])} technologies">{"".join(tech_chip(t) for t in layer["items"])}</ul></li>'
        for i, layer in enumerate(layers))
    return (f'<section class="stack-section" aria-labelledby="stack-title"><div class="section-heading"><div>'
            f'<p class="eyebrow">How it’s built</p><h2 id="stack-title">Tech <em>stack.</em></h2></div></div>'
            f'<ol class="stack">{rows}</ol></section>')


def stack_overview(prefix):
    """About page: the headline tools only (site.json -> stackOverview), in a few simple groups.
    The full, per-layer detail lives on each project page."""
    groups = site.get('stackOverview') or []
    if not groups:
        return ''
    used = {t for p in projects for layer in p.get('stack') or [] for t in layer['items']}
    used |= {t for c in collections for m in c['projects'] for t in m.get('stack', [])}
    rows = ''
    for g in groups:
        for t in g['items']:
            if t not in used:
                raise SystemExit(f'stackOverview lists "{t}", which no project uses')
        chips = ''.join(tech_chip(t) for t in g['items'])
        rows += (f'<li class="stack-layer reveal"><div class="stack-label"><div><h3>{e(g["group"])}</h3></div></div>'
                 f'<ul class="tech-list" aria-label="{e(g["group"])}">{chips}</ul></li>')
    return (f'<section class="section about-section" aria-labelledby="tools-title"><div class="section-heading"><div>'
            f'<p class="eyebrow">Tools I build with</p><h2 id="tools-title">A stack that <em>ships.</em></h2>'
            f'<p class="section-lead">The core of what I use. Each project page shows its full stack.</p></div>'
            f'<a class="text-link" href="{prefix}work/">See the projects {arrow()}</a></div>'
            f'<ul class="stack tech-groups">{rows}</ul></section>')


def principles_section():
    items = site.get('principles') or []
    if not items:
        return ''
    cards = ''.join(f'<li class="principle reveal"><span class="principle-num">{i + 1:02d}</span><h3>{e(x["title"])}</h3><p>{e(x["text"])}</p></li>'
                    for i, x in enumerate(items))
    return (f'<section class="section about-section" aria-labelledby="how-title"><div class="section-heading"><div>'
            f'<p class="eyebrow">How I work</p><h2 id="how-title">A few things I <em>believe.</em></h2></div></div>'
            f'<ol class="principles">{cards}</ol></section>')


def experience_section():
    """Renders only when site.json has entries: {"role", "org", "period", "summary"}."""
    items = site.get('experience') or []
    if not items:
        return ''
    rows = ''.join(f'<li class="timeline-item reveal"><p class="timeline-period">{e(x.get("period", ""))}</p>'
                   f'<h3>{e(x["role"])}<span> · {e(x.get("org", ""))}</span></h3><p>{e(x.get("summary", ""))}</p></li>'
                   for x in items)
    return (f'<section class="section about-section" aria-labelledby="exp-title"><div class="section-heading"><div>'
            f'<p class="eyebrow">Experience</p><h2 id="exp-title">Where I’ve <em>worked.</em></h2></div></div>'
            f'<ol class="timeline">{rows}</ol></section>')


def certifications_section():
    """Renders only when site.json has entries: {"name", "issuer", "year", "url"}."""
    items = site.get('certifications') or []
    if not items:
        return ''
    cards = ''
    for x in items:
        inner = (f'<span class="cert-issuer">{e(x.get("issuer", ""))}</span><h3>{e(x["name"])}</h3>'
                 f'<span class="cert-year">{e(x.get("year", ""))}</span>')
        cards += (f'<li class="cert reveal"><a href="{e(x["url"])}" target="_blank" rel="noopener noreferrer">{inner}'
                  f'<span class="cert-verify">Verify {arrow()}</span></a></li>' if x.get('url') else f'<li class="cert reveal"><div>{inner}</div></li>')
    return (f'<section class="section about-section" aria-labelledby="cert-title"><div class="section-heading"><div>'
            f'<p class="eyebrow">Certifications</p><h2 id="cert-title">Proven, <em>on paper too.</em></h2></div></div>'
            f'<ul class="certs">{cards}</ul></section>')


def page_intro(eyebrow, title, lead):
    return f'<section class="page-intro"><p class="eyebrow">{eyebrow}</p><h1>{title}</h1><p class="lead">{lead}</p></section>'


def write(path, content):
    f = ROOT / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content)
    built.append(path)


built = []

# --- Home ---------------------------------------------------------------------
words = site.get('rotatingWords') or ['reality.']
write('index.html', head(site['title'], 'home', '', '', full_title=True) + f'''<main id="main">
<section class="hero" data-hero>
  <canvas class="particles" data-particles aria-hidden="true"></canvas>
  <div class="hero-copy">
    <p class="eyebrow">Hello, I’m {e(site['name'])}</p>
    <h1 class="hero-title"><span class="sr-only">Ideas, engineered into reality.</span><span aria-hidden="true">Ideas, <span class="soft">engineered</span><br>into <span class="rotator" data-rotate="{e(json.dumps(words))}">{e(words[0])}</span></span></h1>
    <p class="lead">{e(site['intro'])}</p>
    <div class="actions">{button('Explore my work', 'work/')}{button('About me', 'about/', True)}</div>
    <ul class="focus-list" aria-label="Focus areas"><li>Cloud architecture</li><li>Applications</li><li>Automation</li><li>AI-assisted</li></ul>
  </div>
  {portrait('')}
  <button class="motion-toggle" type="button" data-motion-toggle aria-pressed="false">Pause motion</button>
</section>
<section class="section">
  <div class="section-heading reveal"><div><p class="eyebrow">Selected work</p><h2>Ideas in <em>action.</em></h2></div><a class="text-link" href="work/">All projects {arrow()}</a></div>
  {cards()}
</section>
<section class="section">
  <div class="section-heading reveal"><div><p class="eyebrow">What I do</p><h2>From possibility to <em>something real.</em></h2></div><a class="text-link" href="services/">All services {arrow()}</a></div>
  {services('', 'h3')}
</section>
<section class="section home-about reveal">
  <div><p class="eyebrow">About me</p><h2>Curious about what’s possible.<br><em>Focused on making it work.</em></h2></div>
  <div><p>{e(site['about'])}</p><a class="text-link" href="about/">More about me {arrow()}</a></div>
</section>
{cta('')}
</main>
''' + footer(''))

# --- About --------------------------------------------------------------------
write('about/index.html', head('About me', 'about', '../', 'about/', site['about']) + f'''<main id="main">
<section class="about-layout">
  {portrait('../', 'about')}
  <div class="about-copy">
    <p class="eyebrow">A little about me</p>
    <h1>Hi, I’m Ray<span class="dot">.</span><br>I turn <em>what if</em><br>into <em>what’s next.</em></h1>
    <p class="lead">{e(site['about'])}</p>
    <dl class="about-focus"><dt>My focus</dt><dd>Cloud Architecture</dd><dd>Application Development</dd><dd>Automation</dd></dl>
    {button('Let’s bring your idea to life', '../contact/')}
  </div>
</section>
{principles_section()}
{stack_overview('../')}
{experience_section()}
{certifications_section()}
{cta('../')}
</main>
''' + footer('../'))

# --- Services -----------------------------------------------------------------
write('services/index.html', head('Services', 'services', '../', 'services/') + f'''<main id="main" class="page-main">
{page_intro('What I can help with', 'From possibility<br>to <em>something real.</em>', 'Your idea is the starting point. Cloud, applications, automation, and the power of AI help bring it to life.')}
{services('../')}
{cta('../')}
</main>
''' + footer('../'))

# --- Projects index -----------------------------------------------------------
write('work/index.html', head('Projects', 'work', '../', 'work/') + f'''<main id="main" class="page-main">
{page_intro('Selected projects', 'Built to do<br><em>something useful.</em>', 'A collection of applications and automations. Take a look around.')}
{cards('../')}
<p class="collection-note">Some projects are private. Selected screenshots and illustrations offer a look inside.</p>
{cta('../')}
</main>
''' + footer('../'))

# --- Contact ------------------------------------------------------------------
options = '<option value="idea">Bringing an idea to life</option>' + ''.join(
    f'<option value="{e(s["icon"])}">{e(s["title"])}</option>' for s in site['services'])
write('contact/index.html', head('Contact', 'contact', '../', 'contact/') + f'''<main id="main" class="contact-layout">
<section>
  <p class="eyebrow">Let’s connect</p>
  <h1>Big idea?<br>Small question?<br><em>Let’s talk.</em></h1>
  <p class="lead">Tell me what you have in mind. An application, a cloud project, or a workflow that could use a little automation.</p>
  <a class="email-link" href="mailto:{e(site['email'])}">{e(site['email'])} {arrow()}</a>
  <a class="text-link" href="{e(site['github'])}" target="_blank" rel="noopener noreferrer">Find me on GitHub {arrow()}</a>
</section>
<form id="contact-form" data-email="{e(site['email'])}">
  <h2>What are you thinking?</h2>
  <label for="name">Your name</label><input id="name" name="name" autocomplete="name" required placeholder="Name">
  <label for="email">Your email</label><input id="email" name="email" type="email" autocomplete="email" required placeholder="you@example.com">
  <label for="service">I’m interested in</label><select id="service" name="service">{options}</select>
  <label for="message">Your idea</label><textarea id="message" name="message" rows="4" required placeholder="A little about what you’d like to create…"></textarea>
  <button class="button" type="submit">Compose email {arrow()}</button>
  <p class="form-note">Opens your email app with your message filled in. You review and send it there.</p>
  <p id="form-status" role="status"></p>
</form>
</main>
''' + footer('../'))

# --- Project pages ------------------------------------------------------------
# Remove pages for projects that were renamed or deleted (generated folders only).
slugs = {p['slug'] for p in projects} | {c['slug'] for c in collections}
for old in (ROOT / 'projects').glob('*/'):
    if old.name not in slugs and [f.name for f in old.iterdir()] == ['index.html']:
        (old / 'index.html').unlink()
        old.rmdir()
        print(f'Removed stale page: projects/{old.name}/')

sequence = projects + collections
for i, p in enumerate(projects):
    prefix = '../../'
    shots = p['screenshots']
    hero_shot, gallery = '', ''
    for j, s in enumerate(shots):
        img = picture(prefix, s['src'], s['alt'], 'loading="lazy"' if j else 'fetchpriority="high"')
        full = webp_for(s['src']) or s['src']
        # site.js opens these in an in-page lightbox; without JS the link opens the original image.
        link = (f'<a href="{prefix}{e(s["src"])}" data-lightbox data-full="{prefix}{e(full)}" '
                f'data-caption="{e(s["caption"])}" aria-label="View {e(s["caption"])} larger">')
        expand = f'<span>View larger {icon("expand")}</span>'
        if j == 0:
            hero_shot = (f'<figure class="showcase-shot"><div class="window">{window_bar(p)}'
                         f'{link}{img}</a></div><figcaption>{e(s["caption"])}{expand}</figcaption></figure>')
        else:
            gallery += (f'<figure class="showcase-shot reveal">{link}{img}</a>'
                        f'<figcaption>{e(s["caption"])}{expand}</figcaption></figure>')
    if not shots and p.get('art'):
        a = p['art']
        hero_shot = (f'<figure class="showcase-shot"><img class="art" src="{prefix}{e(a["src"])}" alt="{e(a["alt"])}" fetchpriority="high">'
                     f'<figcaption>{e(a["caption"])}<span>Illustration</span></figcaption></figure>')
    elif not shots:
        gallery = f'<div class="coming-project"><span>{e(p["number"])}</span><p>A new project is on its way.</p></div>'
    features = ''
    if p['features']:
        features = '<div class="feature-grid">' + ''.join(
            f'<div class="reveal"><h2>{e(f[0])}</h2><p>{e(f[1])}</p></div>' for f in p['features']) + '</div>'
    links = ''.join(button(label, p[k], external=True) for k, label in [('repository', 'View source'), ('demo', 'Open project')] if p.get(k))
    note = f'<p class="collection-note">{e(p["note"])}</p>' if p.get('note') else ''
    nxt = sequence[(i + 1) % len(sequence)]
    write(f'projects/{p["slug"]}/index.html', head(p['title'], 'work', prefix, f'projects/{p["slug"]}/', p['summary']) + f'''<main id="main" class="project-page">
<a class="text-link back-link" href="../../work/"><span aria-hidden="true">←</span> All projects</a>
<section class="project-intro">
  <p class="eyebrow">{e(p['category'])} <span class="pill">{e(p['visibility'])}</span></p>
  <h1>{e(p['title'])}<span class="dot">.</span></h1>
  <h2>{e(p['subtitle'])}</h2>
  <p class="lead">{e(p['description'])}</p>
  {tags(p.get('tags'))}
  {'<div class="actions">' + links + '</div>' if links else ''}
</section>
{'<div class="gallery-hero">' + hero_shot + '</div>' if hero_shot else ''}
{features}
<div class="gallery">{gallery}</div>
{stack_section(p)}
{note}
<a class="next-project" href="../{e(nxt['slug'])}/"><span>Next project</span><strong>{e(nxt['title'])} {arrow()}</strong></a>
</main>
''' + footer(prefix))

# --- Collection pages ---------------------------------------------------------
# A short overview and a single "Built with" row per project; no screenshots or internals.
for i, c in enumerate(collections):
    prefix = '../../'
    members = ''.join(
        f'<article class="member reveal" aria-labelledby="member-{j}"><div class="member-head">'
        f'<span class="member-num">{j + 1:02d}</span><p class="card-meta"><span>{e(m["category"])}</span></p></div>'
        f'<h2 id="member-{j}">{e(m["title"])}</h2><p class="member-tagline">{e(m["tagline"])}</p>'
        f'<p class="member-summary">{e(m["summary"])}</p>'
        f'<div class="member-stack"><p class="member-stack-label">Built with</p>'
        f'<ul class="tech-list" aria-label="{e(m["title"])} technologies">{"".join(tech_chip(t) for t in m["stack"])}</ul></div></article>'
        for j, m in enumerate(c['projects']))
    nxt = sequence[(len(projects) + i + 1) % len(sequence)]
    write(f'projects/{c["slug"]}/index.html', head(c['title'], 'work', prefix, f'projects/{c["slug"]}/', c['summary']) + f'''<main id="main" class="project-page">
<a class="text-link back-link" href="../../work/"><span aria-hidden="true">←</span> All projects</a>
<section class="project-intro">
  <p class="eyebrow">{e(c['category'])} <span class="pill">{e(c['visibility'])}</span></p>
  <h1>{e(c['title'])}<span class="dot">.</span></h1>
  <h2>{e(c['subtitle'])}</h2>
  <p class="lead">{e(c['description'])}</p>
</section>
<div class="members">{members}</div>
<a class="next-project" href="../{e(nxt['slug'])}/"><span>Next project</span><strong>{e(nxt['title'])} {arrow()}</strong></a>
</main>
''' + footer(prefix))

# --- 404 (served from any path, so links use the absolute base path) ----------
base = site.get('basePath', '/')
write('404.html', head('Page not found', '', base, '404.html') + f'''<main id="main" class="page-main not-found">
{page_intro('Error 404', 'This page took<br>a <em>different path.</em>', 'The page you’re looking for doesn’t exist or has moved.')}
<div class="actions">{button('Back to home', base + 'index.html')}{button('See my projects', base + 'work/', True)}</div>
</main>
''' + footer(base))

print(f'Built {len(built)} pages: ' + ', '.join(built))
