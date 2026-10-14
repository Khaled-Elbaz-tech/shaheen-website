<?php
/** POST do=media_meta — save title/alt/caption overrides into site.json media_meta. */
declare(strict_types=1);

require_perm('media');
$u = current_user();

$key = (string)($_POST['key'] ?? '');
if (!is_valid_slug($key)) { flash('error', 'Invalid asset key.'); redirect(admin_url('media')); }

$site = site_load();
$site['media_meta'][$key] = [
    'title'   => trim((string)($_POST['title'] ?? '')),
    'alt'     => trim((string)($_POST['alt'] ?? '')),
    'caption' => trim((string)($_POST['caption'] ?? '')),
];
try {
    site_save($site);
} catch (Throwable $t) {
    flash('error', 'Could not save site.json: ' . $t->getMessage());
    redirect(admin_url('media'));
}
log_activity($u ? (int)$u['id'] : null, 'media_meta', $key);
flash('success', 'Metadata saved for "' . $key . '".');
redirect(admin_url('media'));
