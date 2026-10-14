<?php
/** POST do=journal_delete — remove a journal entry, then rebuild. */
declare(strict_types=1);

require_perm('journal');
$u = current_user();

$idx = (int)($_POST['idx'] ?? -1);
$site = site_load();
if (!isset($site['journal'][$idx])) { flash('error', 'Entry not found.'); redirect(admin_url('journal')); }
$title = $site['journal'][$idx]['title'] ?? '';
array_splice($site['journal'], $idx, 1);
try { site_save($site); }
catch (Throwable $t) { flash('error', 'Could not save site.json: ' . $t->getMessage()); redirect(admin_url('journal')); }

log_activity($u ? (int)$u['id'] : null, 'journal_delete', $title);
flash('success', 'Journal entry deleted.');
[$code, $out] = rebuild_site();
if ($code !== 0) flash('error', 'Rebuild failed (exit ' . $code . '): ' . trunc($out, 500));
redirect(admin_url('journal'));
