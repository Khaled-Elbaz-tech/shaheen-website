# Ola Magdy Portfolio CMS

PHP 8, no framework, no composer dependencies. SQLite via PDO.

## Run it

Serve the **site root** as the docroot (so `../dist` resolves relatively):

```bash
cd ~/workspace/shaheen-website
php -S localhost:8000
# open http://localhost:8000/admin/
```

Under XAMPP (Windows): put the `shaheen-website` folder in `htdocs` and open
`http://localhost/shaheen-website/admin/`. On Windows the rebuild uses `python`
instead of `python3`.

## First run

With an empty user table, `/admin/` redirects to **first-run setup**: create the
super admin account (name, email, password ≥ 10 chars). There are no default
credentials. Login is rate-limited to 5 attempts / 10 min per IP.

## What it manages

- `content.json` — projects (CRUD, drafts, reorder, revisions, per-project SEO).
  Schema is never changed; the top-level `slides` register is kept in sync.
- `site.json` — hero, studio, approach stages, landscape gallery, journal,
  contact, nav, sections order, SEO, media title/alt/caption overrides.
  Created on first save if the frontend hasn't created it yet.
- `dist/assets/` — media uploads (validated, converted to WebP via GD when
  available). `assets.json` is read-only and never written.
- `admin/db/cms.sqlite` — users, roles, activity log, inquiries, revisions,
  login attempts (gitignored; blocked by `db/.htaccess`).

Every save writes the JSON atomically (temp file + rename) and runs
`python3 build.py`; build output is shown, and a failed build keeps the saved
JSON with an error message.

## Security notes

- All admin pages send `noindex,nofollow,noarchive`. For production also add an
  `.htaccess` in `admin/` restricting access by IP or adding HTTP basic auth in
  front, and serve over HTTPS.
- Every mutating action checks the server-side role matrix in `inc/auth.php`
  (`super_admin` > `editor` > `author` > `viewer`) — not just the UI.
- CSRF tokens on all POST forms; sessions use HttpOnly + SameSite=Lax (+ Secure
  on HTTPS) cookies and are regenerated on login.
