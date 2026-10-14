<?php
/** POST do=setup — create the first super_admin. Only when users table is empty. */
declare(strict_types=1);

if (user_count() > 0) {
    http_response_code(403);
    die('Setup is already complete.');
}

$name = trim((string)($_POST['name'] ?? ''));
$email = strtolower(trim((string)($_POST['email'] ?? '')));
$pw1 = (string)($_POST['password'] ?? '');
$pw2 = (string)($_POST['password2'] ?? '');

$err = null;
if ($name === '' || mb_strlen($name) > 120) $err = 'Please enter your full name.';
elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) $err = 'Please enter a valid email address.';
elseif (mb_strlen($pw1) < 10) $err = 'Password must be at least 10 characters.';
elseif ($pw1 !== $pw2) $err = 'Passwords do not match.';

if ($err) {
    flash('error', $err);
    redirect(admin_url('setup'));
}

$pdo = cms_pdo();
$st = $pdo->prepare("INSERT INTO users (name, email, password_hash, role, active) VALUES (?,?,?,?,1)");
$st->execute([$name, $email, password_hash($pw1, PASSWORD_DEFAULT), 'super_admin']);
$uid = (int)$pdo->lastInsertId();

session_regenerate_id(true);
$_SESSION['uid'] = $uid;
$_SESSION['csrf_token'] = bin2hex(random_bytes(32));
log_activity($uid, 'setup', 'Initial super admin account created: ' . $email);
flash('success', 'Welcome, ' . $name . ' — your admin account is ready.');
redirect(admin_url('dashboard'));
