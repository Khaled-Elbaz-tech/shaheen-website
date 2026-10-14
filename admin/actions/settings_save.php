<?php
/** POST do=settings_save — site name + danger-zone actions (super_admin only). */
declare(strict_types=1);

require_perm('settings');
$u = current_user();

$sub = (string)($_POST['sub'] ?? '');

if ($sub === 'clear_log') {
    cms_pdo()->exec("DELETE FROM activity_log");
    flash('success', 'Activity log cleared.');
    redirect(admin_url('settings'));
}

flash('info', 'Nothing to save.');
redirect(admin_url('settings'));
