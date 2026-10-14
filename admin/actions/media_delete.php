<?php
/** POST do=media_delete — delete an asset file (with "in use" warning handled in the view). */
declare(strict_types=1);

require_perm('media');
$u = current_user();

$key = (string)($_POST['key'] ?? '');
if (!is_valid_slug($key)) { flash('error', 'Invalid asset key.'); redirect(admin_url('media')); }

$uses = media_usage($key);
$force = !empty($_POST['force']);
if ($uses && !$force) {
    flash('error', 'Still in use: ' . implode('; ', array_slice($uses, 0, 4)) . '. Tick "delete anyway" to force.');
    redirect(admin_url('media'));
}

$path = ASSETS_DIR . '/' . $key . '.webp';
if (file_exists($path) && !@unlink($path)) {
    flash('error', 'Could not delete the file (check permissions).');
    redirect(admin_url('media'));
}
// Drop any metadata override.
$site = site_load();
if (isset($site['media_meta'][$key])) {
    unset($site['media_meta'][$key]);
    try { site_save($site); } catch (Throwable $t) {}
}

log_activity($u ? (int)$u['id'] : null, 'media_delete', $key . ($uses ? ' (was in use)' : ''));
flash('success', 'Deleted "' . $key . '". Run Rebuild from Settings if any page referenced it.');
redirect(admin_url('media'));
