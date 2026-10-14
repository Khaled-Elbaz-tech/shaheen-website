<?php
/** POST do=journal_save — create or update a journal entry in site.json, then rebuild. */
declare(strict_types=1);

require_perm('journal');
$u = current_user();

$idx = isset($_POST['idx']) && $_POST['idx'] !== '' ? (int)$_POST['idx'] : null;
$title = trim((string)($_POST['title'] ?? ''));
$date = trim((string)($_POST['date'] ?? ''));
$summary = trim((string)($_POST['summary'] ?? ''));
$link = trim((string)($_POST['link'] ?? ''));
$status = (string)($_POST['status'] ?? 'published');

$errs = [];
if ($title === '') $errs[] = 'Title is required.';
if ($date !== '' && !preg_match('#^\d{4}-\d{2}-\d{2}$#', $date)) $errs[] = 'Date must be YYYY-MM-DD.';
if (!in_array($status, ['published', 'draft'], true)) $status = 'published';
if ($link !== '' && !is_safe_url($link)) $errs[] = 'Link is not a valid/safe URL.';
if ($errs) { foreach ($errs as $eMsg) flash('error', $eMsg); redirect(admin_url('journal')); }

$site = site_load();
// build.py reads j['url']; the shared contract names it 'link' — write both.
$entry = ['title' => $title, 'date' => $date, 'summary' => $summary, 'link' => $link, 'url' => $link, 'status' => $status];
if ($idx === null) {
    $site['journal'][] = $entry;
    $action = 'journal_create';
} else {
    if (!isset($site['journal'][$idx])) { flash('error', 'Entry not found.'); redirect(admin_url('journal')); }
    $site['journal'][$idx] = $entry;
    $action = 'journal_update';
}
try { site_save($site); }
catch (Throwable $t) { flash('error', 'Could not save site.json: ' . $t->getMessage()); redirect(admin_url('journal')); }

log_activity($u ? (int)$u['id'] : null, $action, $title . ' [' . $status . ']');
flash('success', 'Journal entry saved.');
if ($status === 'draft' && !build_supports_journal_drafts()) {
    flash('warn', 'Draft journal entries are stored, but the current build.py shows every entry — this draft will still appear on the site.');
}
[$code, $out] = rebuild_site();
if ($code !== 0) flash('error', 'Rebuild failed (exit ' . $code . '): ' . trunc($out, 500));
redirect(admin_url('journal'));
