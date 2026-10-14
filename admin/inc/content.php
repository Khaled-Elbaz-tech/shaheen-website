<?php
/**
 * Content layer: reads/writes content.json and site.json.
 * - All writes are atomic: JSON encode -> temp file (LOCK_EX) -> rename().
 * - content.json schema is NEVER changed; keys are preserved verbatim.
 * - The top-level "slides" register in content.json is kept in sync:
 *   entries of type "project" are regenerated from their group's data.
 */
declare(strict_types=1);

const SITE_ROOT   = __DIR__ . '/../..';
const CONTENT_JSON = SITE_ROOT . '/content.json';
const SITE_JSON    = SITE_ROOT . '/site.json';
const ASSETS_DIR   = SITE_ROOT . '/dist/assets';
const ASSETS_JSON  = SITE_ROOT . '/assets.json';
const BUILD_PY     = SITE_ROOT . '/build.py';

/* ------------------------------------------------ JSON io */

function json_read_file(string $path): mixed {
    if (!file_exists($path)) return null;
    $raw = file_get_contents($path);
    if ($raw === false) throw new RuntimeException('Cannot read ' . basename($path));
    $data = json_decode($raw, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new RuntimeException('Invalid JSON in ' . basename($path) . ': ' . json_last_error_msg());
    }
    return $data;
}

/** Atomic pretty-printed JSON write (temp + rename). */
function json_write_file(string $path, mixed $data): void {
    $json = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    if ($json === false) throw new RuntimeException('JSON encode failed: ' . json_last_error_msg());
    $tmp = $path . '.tmp.' . bin2hex(random_bytes(6));
    if (file_put_contents($tmp, $json, LOCK_EX) === false) {
        throw new RuntimeException('Cannot write temp file for ' . basename($path));
    }
    chmod($tmp, 0644);
    if (!rename($tmp, $path)) {
        @unlink($tmp);
        throw new RuntimeException('Cannot replace ' . basename($path) . ' (check folder permissions).');
    }
}

/* ------------------------------------------------ content.json */

function content_load(): array {
    $c = json_read_file(CONTENT_JSON);
    if (!is_array($c) || !isset($c['groups'])) {
        throw new RuntimeException('content.json is missing or malformed.');
    }
    return $c;
}

function content_save(array $c): void {
    json_write_file(CONTENT_JSON, $c);
}

function group_by_id(array $c, string $id): ?array {
    foreach ($c['groups'] as $g) {
        if ($g['id'] === $id) return $g;
    }
    return null;
}

function project_status(array $g): string {
    $s = $g['status'] ?? 'published';
    return in_array($s, ['published', 'draft', 'archived'], true) ? $s : 'published';
}

function project_counts(array $c): array {
    $out = ['total' => 0, 'published' => 0, 'draft' => 0, 'archived' => 0];
    foreach ($c['groups'] as $g) {
        $out['total']++;
        $out[project_status($g)]++;
    }
    return $out;
}

function next_project_number(array $c): int {
    $max = 0;
    foreach ($c['groups'] as $g) $max = max($max, (int)($g['number'] ?? 0));
    return $max + 1;
}

/**
 * Keep the top-level "slides" register consistent with the groups.
 * - Entries with type=project belonging to the changed group are
 *   regenerated from the group's own slide data (same fields).
 * - Entries of all other types are left untouched and keep position.
 * - On delete the group's entries are removed.
 * - On create the entries are appended after the last project entry.
 */
function sync_register(array &$c, ?array $group = null, ?string $deletedId = null): void {
    if (!isset($c['slides']) || !is_array($c['slides'])) $c['slides'] = [];

    $project_entries = function (array $g): array {
        $out = [];
        foreach (($g['slides'] ?? []) as $s) {
            $caps = $s['captions'] ?? '';
            $out[] = [
                'type'     => 'project',
                'group'    => $g['id'],
                'title'    => $s['title'] ?? '',
                'body'     => $s['body'] ?? '',
                'images'   => array_values($s['images'] ?? []),
                'captions' => $caps,
                'layout'   => $s['layout'] ?? 'single',
            ];
        }
        return $out;
    };

    $new = [];
    $inserted = false;
    foreach ($c['slides'] as $entry) {
        $isProject = is_array($entry) && ($entry['type'] ?? '') === 'project';
        $gid = $isProject ? ($entry['group'] ?? '') : '';
        if ($isProject && $deletedId !== null && $gid === $deletedId) {
            continue; // drop removed project's register entries
        }
        if ($isProject && $group !== null && $gid === $group['id']) {
            if (!$inserted) { // replace once; skip duplicates of the same group
                foreach ($project_entries($group) as $pe) $new[] = $pe;
                $inserted = true;
            }
            continue;
        }
        $new[] = $entry;
    }
    if ($group !== null && !$inserted && $deletedId === null) {
        // Brand-new project: insert after the last project entry (before closing/profile/register).
        $pos = count($new);
        foreach ($new as $i => $entry) {
            if (is_array($entry) && ($entry['type'] ?? '') === 'project') $pos = $i + 1;
        }
        array_splice($new, $pos, 0, $project_entries($group));
    }
    $c['slides'] = $new;
}

/** Store the previous group JSON as a restorable revision. */
function revision_store(string $entity, string $entityId, array $data, ?int $userId): void {
    $pdo = cms_pdo();
    $st = $pdo->prepare("INSERT INTO revisions (entity, entity_id, data, user_id) VALUES (?,?,?,?)");
    $st->execute([$entity, $entityId, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), $userId]);
    // Keep the last 25 revisions per entity to bound growth.
    $pdo->exec("DELETE FROM revisions WHERE entity=" . $pdo->quote($entity) .
        " AND entity_id=" . $pdo->quote($entityId) .
        " AND id NOT IN (SELECT id FROM revisions WHERE entity=" . $pdo->quote($entity) .
        " AND entity_id=" . $pdo->quote($entityId) . " ORDER BY id DESC LIMIT 25)");
}

function revisions_for(string $entity, string $entityId, int $limit = 25): array {
    $st = cms_pdo()->prepare("SELECT r.*, u.name AS user_name FROM revisions r LEFT JOIN users u ON u.id=r.user_id WHERE r.entity=? AND r.entity_id=? ORDER BY r.id DESC LIMIT ?");
    $st->execute([$entity, $entityId, $limit]);
    return $st->fetchAll();
}

/* ------------------------------------------------ site.json */

function site_defaults(): array {
    // Mirrors build.py DEFAULT_SITE (the frontend agent's build). The admin
    // never invents a different shape: saved site.json values always win
    // via deep_merge(), and saves below preserve this exact structure.
    return [
        'hero' => [
            'headline' => '', 'descriptor' => '', 'image' => '', 'project_id' => '', 'alt' => '',
        ],
        'intro' => ['eyebrow' => '', 'statement' => '', 'copy' => ''],
        'studio' => [
            'headline' => '', 'intro' => '', 'bio' => '', 'philosophy' => '',
            'image' => '', 'image_alt' => '', 'image_caption' => '',
        ],
        'approach' => [
            'headline' => '', 'intro' => '',
            'stages' => [
                ['n' => '01', 'title' => 'Listen',  'text' => ''],
                ['n' => '02', 'title' => 'Explore', 'text' => ''],
                ['n' => '03', 'title' => 'Shape',   'text' => ''],
                ['n' => '04', 'title' => 'Deliver', 'text' => ''],
            ],
        ],
        'landscape_gallery' => ['headline' => '', 'intro' => '', 'images' => []],
        'journal' => [],
        'contact' => ['headline' => '', 'copy' => '', 'email' => '', 'socials' => []],
        'nav' => [
            ['label' => 'Work', 'href' => '#work'],
            ['label' => 'Studio', 'href' => '#studio'],
            ['label' => 'Approach', 'href' => '#approach'],
            ['label' => 'Journal', 'href' => '#journal'],
            ['label' => 'Contact', 'href' => '#contact'],
        ],
        // Flat ordered id list, exactly as build.py iterates it.
        'sections_order' => ['hero', 'intro', 'work', 'landscape', 'studio', 'approach', 'journal', 'contact'],
        // Admin-only: ids the editor disabled. build.py does not read this yet
        // (it renders every id in sections_order); the UI warns about that.
        'sections_disabled' => [],
        'seo' => ['title' => '', 'description' => '', 'og_image' => ''],
        'media_meta' => new stdClass(), // encoded as {} — key -> {title,alt,caption}
    ];
}

/** Section id => human label for the sections editor. */
function site_section_labels(): array {
    return [
        'hero' => 'Hero', 'intro' => 'Intro', 'work' => 'Work', 'landscape' => 'Landscape gallery',
        'studio' => 'Studio / About', 'approach' => 'Approach', 'journal' => 'Journal', 'contact' => 'Contact',
    ];
}

/**
 * Full ordered section list for the editor: [['id'=>..,'label'=>..,'enabled'=>bool]].
 * Reconciles sections_order (flat strings) with sections_disabled.
 */
function site_sections_editor(array $site): array {
    $labels = site_section_labels();
    $order = $site['sections_order'] ?? [];
    if (!is_array($order)) $order = [];
    // Tolerate the old dict shape [{id,label,enabled}] if ever written.
    $ids = [];
    $enabledMap = [];
    foreach ($order as $entry) {
        if (is_array($entry)) {
            $ids[] = (string)($entry['id'] ?? '');
            $enabledMap[(string)($entry['id'] ?? '')] = !isset($entry['enabled']) || !empty($entry['enabled']);
        } else {
            $ids[] = (string)$entry;
        }
    }
    $disabled = $site['sections_disabled'] ?? [];
    if (!is_array($disabled)) $disabled = [];
    // Any known section missing from the order gets appended (never lost).
    foreach (array_keys($labels) as $id) {
        if (!in_array($id, $ids, true)) $ids[] = $id;
    }
    $out = [];
    foreach ($ids as $id) {
        if ($id === '') continue;
        $en = $enabledMap[$id] ?? !in_array($id, $disabled, true);
        $out[] = ['id' => $id, 'label' => $labels[$id] ?? $id, 'enabled' => $en];
    }
    return $out;
}

/** Deep-merge saved site.json over defaults so new fields always exist. */
function site_load(): array {
    $saved = json_read_file(SITE_JSON);
    $merged = deep_merge(site_defaults(), is_array($saved) ? $saved : []);
    // media_meta must stay a map even after merge.
    $mm = $merged['media_meta'] ?? [];
    if ($mm instanceof stdClass) $mm = (array)$mm;
    $merged['media_meta'] = is_array($mm) ? $mm : [];
    return $merged;
}

function site_save(array $site): void {
    // Keep media_meta an object ({}) in JSON when it has no entries.
    if (isset($site['media_meta']) && $site['media_meta'] === []) {
        $site['media_meta'] = new stdClass();
    }
    json_write_file(SITE_JSON, $site);
}

function deep_merge(array $base, array $over): array {
    foreach ($over as $k => $v) {
        if (is_array($v) && isset($base[$k]) && is_array($base[$k]) && !array_is_list($v) && !array_is_list($base[$k])) {
            $base[$k] = deep_merge($base[$k], $v);
        } else {
            $base[$k] = $v;
        }
    }
    return $base;
}

/** Journal helpers (journal lives in site.json). */
function journal_list(array $site): array {
    return is_array($site['journal'] ?? null) ? $site['journal'] : [];
}

/* ------------------------------------------------ media */

function assets_meta(): array {
    $a = json_read_file(ASSETS_JSON);
    return is_array($a) ? $a : [];
}

/** All webp keys in dist/assets, newest first, with dimensions/size. */
function media_list(): array {
    $meta = assets_meta();
    $site = site_load();
    $over = $site['media_meta'] ?? [];
    $files = glob(ASSETS_DIR . '/*.webp') ?: [];
    $out = [];
    foreach ($files as $f) {
        $key = basename($f, '.webp');
        $m = $meta[$key] ?? [];
        $size = @getimagesize($f);
        $o = is_array($over[$key] ?? null) ? $over[$key] : [];
        $out[] = [
            'key'      => $key,
            'file'     => basename($f),
            'width'    => $m['width'] ?? ($size[0] ?? null),
            'height'   => $m['height'] ?? ($size[1] ?? null),
            'bytes'    => filesize($f),
            'mtime'    => filemtime($f),
            'title'    => $o['title'] ?? ($m['original_text'] ?? ''),
            'alt'      => $o['alt'] ?? '',
            'caption'  => $o['caption'] ?? '',
            'in_meta'  => isset($meta[$key]),
        ];
    }
    usort($out, fn($a, $b) => $b['mtime'] <=> $a['mtime']);
    return $out;
}

/** Where (content.json / site.json) is an asset key referenced? Returns list of "project: id" / "site: section". */
function media_usage(string $key): array {
    $uses = [];
    try {
        $c = content_load();
        foreach ($c['groups'] as $g) {
            $found = false;
            if (($g['hero'] ?? '') === $key) $found = true;
            foreach (($g['slides'] ?? []) as $s) {
                if (in_array($key, $s['images'] ?? [], true)) { $found = true; break; }
            }
            if ($found) $uses[] = 'Project: ' . ($g['title'] ?? $g['id']) . ' (' . $g['id'] . ')';
        }
    } catch (Throwable $t) {}
    $site = site_load();
    $paths = [
        'hero.image' => $site['hero']['image'] ?? '',
        'studio.image' => $site['studio']['image'] ?? '',
        'seo.og_image' => $site['seo']['og_image'] ?? '',
    ];
    foreach ($paths as $label => $v) {
        if ($v === $key) $uses[] = 'Site: ' . $label;
    }
    foreach (($site['landscape_gallery']['images'] ?? []) as $img) {
        if (($img['key'] ?? '') === $key) $uses[] = 'Site: landscape gallery';
    }
    return $uses;
}

/* ------------------------------------------------ rebuild */

function build_supports_status(): bool {
    // The frontend agent's build.py may filter "status": "draft".
    // Until it does, warn that drafts will still be published.
    if (!file_exists(BUILD_PY)) return false;
    $src = (string)@file_get_contents(BUILD_PY);
    return str_contains($src, 'status') && str_contains($src, 'draft');
}

/** Does build.py honour disabled sections / nav items? */
function build_supports_disabled(): bool {
    if (!file_exists(BUILD_PY)) return false;
    $src = (string)@file_get_contents(BUILD_PY);
    return str_contains($src, 'sections_disabled') || str_contains($src, "'enabled'");
}

/** Does build.py hide draft journal entries? */
function build_supports_journal_drafts(): bool {
    if (!file_exists(BUILD_PY)) return false;
    $src = (string)@file_get_contents(BUILD_PY);
    return (bool)preg_match("/journal.{0,200}draft|draft.{0,200}journal/is", $src);
}

/**
 * Run build.py. Returns [exit_code, output].
 * Never throws: callers show output and keep the JSON already written.
 */
function rebuild_site(): array {
    if (!function_exists('exec') && !function_exists('shell_exec')) {
        return [127, 'PHP exec() is disabled on this host — please run build.py manually.'];
    }
    if (!file_exists(BUILD_PY)) {
        return [127, 'build.py not found at ' . BUILD_PY];
    }
    // Windows/XAMPP ships `python`, Linux ships `python3`.
    $py = (PHP_OS_FAMILY === 'Windows') ? 'python' : 'python3';
    $cmd = (PHP_OS_FAMILY === 'Windows')
        ? 'cd /d "' . SITE_ROOT . '" && ' . $py . ' build.py 2>&1'
        : 'cd ' . escapeshellarg(SITE_ROOT) . ' && ' . escapeshellcmd($py) . ' ' . escapeshellarg('build.py') . ' 2>&1';
    $out = [];
    $code = 1;
    @exec($cmd, $out, $code);
    return [$code, implode("\n", $out)];
}
