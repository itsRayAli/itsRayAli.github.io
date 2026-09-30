# Ray Ali — portfolio

A hand-built static portfolio for GitHub Pages: Home, About, Services, Projects, Contact, a page per project, and a 404 page. No framework, no npm install.

## Preview and edit

```sh
python3 scripts/build.py
python3 -m http.server 8000 --bind 127.0.0.1   # open http://127.0.0.1:8000/
```

- `site.json`: name, title, header tagline and status pill, bio, email, GitHub, services, the hero's rotating words, and the About page content (`principles`, `experience`, `certifications`). It also holds the `tech` catalog: `"Name": ["monogram", "#brandcolour", "group"]`.
- `projects.json`: one entry per project. Re-run the build after edits.
- `assets/style.css` and `assets/site.js`: design and progressive enhancements (header, scroll reveal, rotating headline, particle canvas, motion toggle, contact form). All pages work without JavaScript.

## Adding a project

Put screenshots in `assets/<project>/` and add an entry to `projects.json`:

```json
{
  "slug": "my-project", "number": "04",
  "title": "…", "subtitle": "…", "summary": "…", "description": "…",
  "category": "Application / …", "visibility": "Private project",
  "tags": ["…"],
  "features": [["Heading", "One-line detail."]],
  "screenshots": [{"src": "assets/<project>/shot.png", "alt": "…", "caption": "01 / …"}],
  "art": null, "cover": null,
  "note": null, "repository": null, "demo": null
}
```

`cover` (`{"src", "alt"}`) sets the image on the project's card when a screenshot looks too busy there. World Cup uses `assets/worldcup/cover.svg`. The project page still leads with the real screenshots.

Screenshots open in an in-page lightbox with arrow-key and swipe navigation and a zoom for wide images. If you have `cwebp` installed (`brew install webp`), the build writes a WebP copy of each PNG/JPEG screenshot next to the original and serves it with the original as a fallback. Commit the `.webp` files. CI doesn't have `cwebp`, so it uses the committed copies.

The slug becomes the URL (`/projects/my-project/`). Order in the file is the order on the site. Projects with screenshots become full-width feature cards that alternate sides. The first screenshot is the card cover (cropped to 16:10 from the top) and the framed hero image on the project page. With no screenshots, set `art` to an illustration (`{"src", "alt", "caption"}`) instead, as Edgewise does. Entries with neither render as "coming soon" placeholders. Set `repository` or `demo` to a URL to show those buttons. The build deletes pages for slugs that no longer exist.

The "See my work" pill in the homepage hero counts projects that have a screenshot or illustration.

## About page and tech stack

Each project's `stack` is a list of layers (`{"layer", "note", "items": [...]}`) drawn on its page as a connected diagram. Every item must exist in `site.json` → `tech`, or the build stops with a message. The About page combines all project stacks into one grouped overview automatically.

Experience and certifications render only once filled in:

```json
"experience": [{"role": "…", "org": "…", "period": "2022 – now", "summary": "…"}],
"certifications": [{"name": "…", "issuer": "…", "year": "2025", "url": "https://…"}]
```

## GitHub Pages

`.github/workflows/pages.yml` builds the site and deploys only the public folders. The source PNG portraits are excluded from the deploy. Only the optimised JPEG is served.

1. The site serves at https://rayali.dev (custom domain, DNS on Cloudflare in DNS-only mode, HTTPS certificate from GitHub). https://itsrayali.github.io redirects there.
2. Push to `main`.
3. Under Settings → Pages, set Source to **GitHub Actions**.

For a repository subpath (e.g. `/portfolio/`), set `basePath` in `site.json` to `/portfolio/` so `404.html` and social-preview URLs resolve. All other links are relative.

## Assets

`assets/ray-portrait-noir.jpg` is a compressed copy of the AI-generated portrait `ray-portrait-noir.png` (provenance in `docs/portrait-noir-generation.md`). Light mode uses `assets/ray-portrait-light.webp`, a transparent cutout of the same portrait. To regenerate it after changing the portrait (macOS 14+):

```sh
swiftc -O scripts/portrait-cutout.swift -o /tmp/cutout
/tmp/cutout assets/ray-portrait-noir.png /tmp/cut.png
cwebp -q 84 -alpha_q 90 -m 6 /tmp/cut.png -o assets/ray-portrait-light.webp
``` World Cup and RayCast screenshots were supplied by Ray. `assets/edgewise/edgewise-illustration.svg` is a hand-drawn illustration, not a product screenshot. Google Fonts (Manrope, DM Sans) load from Google, with system fallbacks.
