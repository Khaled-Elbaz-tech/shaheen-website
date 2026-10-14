<?php
/** POST do=rebuild — run build.py manually and show its output. */
declare(strict_types=1);

require_perm('rebuild');
$u = current_user();

[$code, $out] = rebuild_site();
log_activity($u ? (int)$u['id'] : null, 'rebuild', 'Manual rebuild, exit ' . $code);
if ($code === 0) {
    flash('success', 'Site rebuilt successfully.');
} else {
    flash('error', 'Rebuild failed (exit ' . $code . ').');
}
$_SESSION['build_output'] = $out;
redirect(admin_url('settings'));
