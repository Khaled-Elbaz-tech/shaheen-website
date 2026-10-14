<?php
/** POST do=user_save — create or update a user (super_admin only). */
declare(strict_types=1);

require_perm('users');
$u = current_user();

$id = isset($_POST['id']) && $_POST['id'] !== '' ? (int)$_POST['id'] : null;
$name = trim((string)($_POST['name'] ?? ''));
$email = strtolower(trim((string)($_POST['email'] ?? '')));
$role = (string)($_POST['role'] ?? 'viewer');
$active = !empty($_POST['active']);
$pw = (string)($_POST['password'] ?? '');

$errs = [];
if ($name === '' || mb_strlen($name) > 120) $errs[] = 'Name is required.';
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) $errs[] = 'Valid email is required.';
if (!in_array($role, CMS_ROLES, true)) $errs[] = 'Invalid role.';
if ($id === null && mb_strlen($pw) < 10) $errs[] = 'Password must be at least 10 characters.';
if ($id !== null && $pw !== '' && mb_strlen($pw) < 10) $errs[] = 'New password must be at least 10 characters.';

$pdo = cms_pdo();
// Email uniqueness.
$st = $pdo->prepare("SELECT id FROM users WHERE email=? AND id<>? LIMIT 1");
$st->execute([$email, $id ?? 0]);
if ($st->fetch()) $errs[] = 'That email is already used by another user.';

// Never deactivate/demote the last active super_admin.
if ($id !== null) {
    $target = get_user_by_id($id);
    if (!$target) $errs[] = 'User not found.';
    else {
        $losing = (!$active || $role !== 'super_admin') && $target['role'] === 'super_admin' && (int)$target['active'] === 1;
        if ($losing) {
            $n = (int)$pdo->query("SELECT COUNT(*) FROM users WHERE role='super_admin' AND active=1 AND id<>" . $id)->fetchColumn();
            if ($n === 0) $errs[] = 'Cannot deactivate or demote the last active super admin.';
        }
    }
}

if ($errs) { foreach ($errs as $eMsg) flash('error', $eMsg); redirect(admin_url('users')); }

if ($id === null) {
    $st = $pdo->prepare("INSERT INTO users (name, email, password_hash, role, active) VALUES (?,?,?,?,?)");
    $st->execute([$name, $email, password_hash($pw, PASSWORD_DEFAULT), $role, $active ? 1 : 0]);
    log_activity($u ? (int)$u['id'] : null, 'user_create', $email . ' [' . $role . ']');
    flash('success', 'User created.');
} else {
    if ($pw !== '') {
        $st = $pdo->prepare("UPDATE users SET name=?, email=?, role=?, active=?, password_hash=? WHERE id=?");
        $st->execute([$name, $email, $role, $active ? 1 : 0, password_hash($pw, PASSWORD_DEFAULT), $id]);
    } else {
        $st = $pdo->prepare("UPDATE users SET name=?, email=?, role=?, active=? WHERE id=?");
        $st->execute([$name, $email, $role, $active ? 1 : 0, $id]);
    }
    log_activity($u ? (int)$u['id'] : null, 'user_update', $email . ' [' . $role . ']');
    flash('success', 'User updated.');
}
redirect(admin_url('users'));
