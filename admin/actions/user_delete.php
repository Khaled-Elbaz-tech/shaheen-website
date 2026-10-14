<?php
/** POST do=user_delete — delete a user (super_admin only). Guards self + last super_admin. */
declare(strict_types=1);

require_perm('users');
$u = current_user();

$id = (int)($_POST['id'] ?? 0);
$target = get_user_by_id($id);
if (!$target) { flash('error', 'User not found.'); redirect(admin_url('users')); }
if ($id === (int)$u['id']) { flash('error', 'You cannot delete your own account.'); redirect(admin_url('users')); }
if ($target['role'] === 'super_admin' && (int)$target['active'] === 1) {
    $n = (int)cms_pdo()->query("SELECT COUNT(*) FROM users WHERE role='super_admin' AND active=1 AND id<>" . $id)->fetchColumn();
    if ($n === 0) { flash('error', 'Cannot delete the last active super admin.'); redirect(admin_url('users')); }
}

$st = cms_pdo()->prepare("DELETE FROM users WHERE id=?");
$st->execute([$id]);
log_activity((int)$u['id'], 'user_delete', $target['email']);
flash('success', 'User deleted.');
redirect(admin_url('users'));
