<?php
/** POST do=seo_save — site.json seo{} + per-project meta fields, then rebuild. */
declare(strict_types=1);

require_perm('seo');
$u = current_user();

$site = site_load();
$site['seo']['title']       = trim((string)($_POST['seo_title'] ?? ''));
$site['seo']['description'] = trim((string)($_POST['seo_description'] ?? ''));
$og = trim((string)($_POST['seo_og_image'] ?? ''));
if ($og !== '' && !is_valid_slug($og)) {
    flash('error', 'OG image key is invalid — pick it from the media picker.');
    redirect(admin_url('seo'));
}
$site['seo']['og_image'] = $og;
try { site_save($site); }
catch (Throwable $t) { flash('error', 'Could not save site.json: ' . $t->getMessage()); redirect(admin_url('seo')); }

// Per-project meta (stored on the group; build.py ignores unknown keys safely).
$c = content_load();
$changed = 0;
foreach ($c['groups'] as $i => $g) {
    $id = $g['id'];
    if (!isset($_POST['pmt'][$id])) continue;
    $mt = trim((string)($_POST['pmt'][$id] ?? ''));
    $md = trim((string)($_POST['pmd'][$id] ?? ''));
    if ($mt !== '') $c['groups'][$i]['meta_title'] = $mt; else unset($c['groups'][$i]['meta_title']);
    if ($md !== '') $c['groups'][$i]['meta_description'] = $md; else unset($c['groups'][$i]['meta_description']);
    $changed++;
}
try { content_save($c); }
catch (Throwable $t) { flash('error', 'Could not save content.json: ' . $t->getMessage()); redirect(admin_url('seo')); }

log_activity($u ? (int)$u['id'] : null, 'seo_update', 'Site SEO + ' . $changed . ' project metas');
flash('success', 'SEO saved.');
[$code, $out] = rebuild_site();
if ($code !== 0) flash('error', 'Rebuild failed (exit ' . $code . '): ' . trunc($out, 500));
redirect(admin_url('seo'));
