<?php
/** POST do=nav_save — save site.json nav[] (label/href, ordered), then rebuild.
 *  Shape matches build.py: [{label, href}]. Disabling is stored as
 *  "enabled": false on the item (admin-only until the build honours it).
 */
declare(strict_types=1);

require_perm('nav');
$u = current_user();

$nav = [];
$disabled = 0;
foreach ((array)($_POST['nav_label'] ?? []) as $i => $label) {
    $label = trim((string)$label);
    $href = trim((string)($_POST['nav_href'][$i] ?? ''));
    if ($label === '' && $href === '') continue;
    if ($label === '' || $href === '') {
        flash('error', 'Every nav item needs both a label and a link.');
        redirect(admin_url('nav'));
    }
    if (!is_safe_url($href)) {
        flash('error', 'Nav link "' . $label . '" is not a safe URL (javascript:/data: blocked).');
        redirect(admin_url('nav'));
    }
    $item = ['label' => $label, 'href' => $href];
    if (empty($_POST['nav_enabled'][$i])) {
        $item['enabled'] = false; // kept for the admin; build.py ignores it for now
        $disabled++;
    }
    $nav[] = $item;
}
if (!$nav) { flash('error', 'Navigation cannot be empty.'); redirect(admin_url('nav')); }

$site = site_load();
$site['nav'] = $nav;
try { site_save($site); }
catch (Throwable $t) { flash('error', 'Could not save site.json: ' . $t->getMessage()); redirect(admin_url('nav')); }

log_activity($u ? (int)$u['id'] : null, 'nav_update', count($nav) . ' nav items');
flash('success', 'Navigation saved.');
if ($disabled && !build_supports_disabled()) {
    flash('warn', 'Disabled nav items are stored, but the current build.py renders every nav item — they will still appear on the site.');
}
[$code, $out] = rebuild_site();
if ($code !== 0) flash('error', 'Rebuild failed (exit ' . $code . '): ' . trunc($out, 500));
redirect(admin_url('nav'));
