<?php
/** POST do=project_save — create or update a project in content.json, then rebuild. */
declare(strict_types=1);

require_perm('projects');

$u = current_user();
$isNew = empty($_POST['id']);
$id = $isNew ? '' : (string)$_POST['id'];
$slugIn = trim((string)($_POST['slug'] ?? ''));

$title    = trim((string)($_POST['title'] ?? ''));
$location = trim((string)($_POST['location'] ?? ''));
$category = trim((string)($_POST['category'] ?? ''));
$body     = (string)($_POST['body'] ?? '');
$hero     = trim((string)($_POST['hero'] ?? ''));
$status   = (string)($_POST['status'] ?? 'published');
$number   = (int)($_POST['number'] ?? 0);
$metaTitle = trim((string)($_POST['meta_title'] ?? ''));
$metaDesc  = trim((string)($_POST['meta_description'] ?? ''));

$errs = [];
if ($title === '') $errs[] = 'Title is required.';
if ($location === '') $errs[] = 'Location is required.';
if ($category === '') $errs[] = 'Category is required.';
if (!in_array($status, ['published', 'draft', 'archived'], true)) $status = 'published';
// Publishing-tab shortcut buttons override the status select.
if (!empty($_POST['status_btn']) && in_array($_POST['status_btn'], ['published', 'draft', 'archived'], true)) {
    $status = $_POST['status_btn'];
}
if ($hero !== '' && !is_valid_slug($hero)) $errs[] = 'Hero image key is invalid. Pick it from the media picker.';
if ($number < 1) $number = 1;

// Authors may not archive or delete.
if ($u['role'] === 'author' && $status === 'archived') {
    $status = 'published';
    $errs[] = 'Authors cannot archive projects — saved as published instead.';
}

$c = content_load();

if ($isNew) {
    $slug = $slugIn !== '' ? $slugIn : slugify($title);
    if (!is_valid_slug($slug)) {
        $errs[] = 'Slug must be lowercase letters, digits and hyphens (min 2 chars).';
    } elseif (group_by_id($c, $slug)) {
        $errs[] = 'A project with that slug already exists.';
    }
    $id = $slug;
} else {
    if (!group_by_id($c, $id)) $errs[] = 'Project not found.';
}

// Slides: normalize, validate image/caption counts (build.py raises on mismatch).
$slides = [];
$rawSlides = $_POST['slides'] ?? [];
if (is_array($rawSlides)) {
    ksort($rawSlides);
    foreach ($rawSlides as $rs) {
        if (!is_array($rs)) continue;
        $st = trim((string)($rs['title'] ?? ''));
        $sb = (string)($rs['body'] ?? '');
        $imgs = array_values(array_filter(array_map('trim', (array)($rs['images'] ?? [])), fn($v) => $v !== ''));
        $capsRaw = (string)($rs['captions'] ?? '');
        $caps = $capsRaw === '' ? [] : preg_split('/\r\n|\r|\n/', $capsRaw);
        $caps = array_map('trim', $caps);
        // Drop trailing empties so "one caption for one image" stays a string.
        while (count($caps) && end($caps) === '') array_pop($caps);
        if ($st === '' && $sb === '' && !$imgs) continue; // empty row
        if (!$imgs) $errs[] = 'Chapter "' . ($st ?: 'untitled') . '" needs at least one image.';
        foreach ($imgs as $k) {
            if (!is_valid_slug($k) || !file_exists(ASSETS_DIR . '/' . $k . '.webp')) {
                $errs[] = 'Image key "' . $k . '" does not exist in the media library.';
            }
        }
        // build.py requires len(captions) == len(images).
        $n = count($imgs);
        if (count($caps) > $n) $caps = array_slice($caps, 0, $n);
        while (count($caps) < $n) $caps[] = '';
        $slides[] = [
            'title'    => $st,
            'body'     => $sb,
            'images'   => $imgs,
            'captions' => $n === 1 ? $caps[0] : $caps,
            'layout'   => in_array($rs['layout'] ?? '', ['single', 'pair', 'stack'], true) ? $rs['layout'] : 'single',
            'anchor'   => trim((string)($rs['anchor'] ?? '')),
        ];
    }
}
if (!$slides) $errs[] = 'Add at least one chapter with an image.';

if ($errs) {
    foreach ($errs as $eMsg) flash('error', $eMsg);
    redirect($isNew ? admin_url('project_edit') : admin_url('project_edit', ['id' => $id]));
}

// Build the group record — preserve unknown/legacy keys (start, end, …) on update.
$group = null; $idx = null;
foreach ($c['groups'] as $i => $g) {
    if ($g['id'] === $id) { $group = $g; $idx = $i; break; }
}
$oldGroup = $group;

if ($group === null) {
    $group = ['id' => $id, 'start' => 0, 'end' => 0];
}
$group['title']    = $title;
$group['location'] = $location;
$group['category'] = $category;
$group['hero']     = $hero !== '' ? $hero : ($group['hero'] ?? '');
$group['body']     = $body;
$group['slides']   = $slides;
$group['number']   = $number;
$group['status']   = $status;
if ($metaTitle !== '') $group['meta_title'] = $metaTitle; else unset($group['meta_title']);
if ($metaDesc !== '') $group['meta_description'] = $metaDesc; else unset($group['meta_description']);

if ($oldGroup !== null && $idx !== null) {
    revision_store('project', $id, $oldGroup, $u ? (int)$u['id'] : null);
    $c['groups'][$idx] = $group;
    $action = 'project_update';
    $msg = 'Project updated.';
} else {
    $c['groups'][] = $group;
    $action = 'project_create';
    $msg = 'Project created.';
}

sync_register($c, $group);

try {
    content_save($c);
} catch (Throwable $t) {
    flash('error', 'Could not save content.json: ' . $t->getMessage());
    redirect(admin_url('project_edit', ['id' => $id]));
}

log_activity($u ? (int)$u['id'] : null, $action, $id . ' — ' . $title . ' [' . $status . ']');
flash('success', $msg . ' Site rebuilt below.');

if ($status !== 'published' && !build_supports_status()) {
    flash('warn', 'Heads up: the current build.py does not filter by status, so this ' . $status .
        ' project will still appear on the public site until the build supports drafts.');
}

[$code, $out] = rebuild_site();
if ($code !== 0) {
    flash('error', 'Rebuild failed (exit ' . $code . '). Your content was saved; fix the build and rebuild from Settings. Output: ' . trunc($out, 600));
} else {
    log_activity($u ? (int)$u['id'] : null, 'rebuild', 'After ' . $action . ' ' . $id);
}

redirect(admin_url('project_edit', ['id' => $id, 'rebuilt' => $code === 0 ? '1' : '0']));

function slugify(string $s): string {
    $s = strtolower(trim($s));
    $s = preg_replace('#[^a-z0-9]+#', '-', $s);
    $s = trim($s, '-');
    return $s === '' ? 'project' : mb_substr($s, 0, 80);
}
