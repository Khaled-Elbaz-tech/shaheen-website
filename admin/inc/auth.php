<?php
/**
 * Authentication & authorization.
 * - Session with secure cookie flags, regenerated on login.
 * - Password hashing via password_hash()/password_verify().
 * - Role permission matrix; every mutating action must call require_perm().
 */
declare(strict_types=1);

const CMS_ROLES = ['super_admin', 'editor', 'author', 'viewer'];

/** permission => roles allowed */
const CMS_PERMS = [
    'projects'        => ['super_admin', 'editor', 'author'], // create/edit projects
    'projects_delete' => ['super_admin', 'editor'],          // delete/duplicate/archive projects
    'media'           => ['super_admin', 'editor', 'author'],
    'journal'         => ['super_admin', 'editor', 'author'],
    'pages'           => ['super_admin', 'editor'],           // site.json sections
    'nav'             => ['super_admin', 'editor'],
    'seo'             => ['super_admin', 'editor'],
    'inquiries'       => ['super_admin', 'editor'],
    'users'           => ['super_admin'],
    'settings'        => ['super_admin'],
    'rebuild'         => ['super_admin', 'editor'],
    'activity'        => ['super_admin', 'editor', 'author', 'viewer'],
];

function session_boot(): void {
    if (session_status() === PHP_SESSION_ACTIVE) return;
    $secure = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
    session_set_cookie_params([
        'lifetime' => 0,
        'path'     => '/',
        'httponly' => true,
        'samesite' => 'Lax',
        'secure'   => $secure,
    ]);
    session_name('shaheen_cms');
    session_start();
}

function current_user(): ?array {
    if (empty($_SESSION['uid'])) return null;
    $u = get_user_by_id((int)$_SESSION['uid']);
    if (!$u || !(int)$u['active']) {
        unset($_SESSION['uid']);
        return null;
    }
    return $u;
}

function is_logged_in(): bool {
    return current_user() !== null;
}

function can(string $perm): bool {
    $u = current_user();
    if (!$u) return false;
    if ($u['role'] === 'super_admin') return true; // belt & braces
    $roles = CMS_PERMS[$perm] ?? [];
    return in_array($u['role'], $roles, true);
}

function require_login(): void {
    if (!is_logged_in()) redirect(admin_url('login'));
}

function require_perm(string $perm): void {
    require_login();
    if (!can($perm)) {
        http_response_code(403);
        die('Forbidden: your role does not allow this action.');
    }
}

function attempt_login(string $email, string $password): array {
    $ip = client_ip();
    if (login_attempts_recent($ip) >= 5) {
        return ['ok' => false, 'error' => 'Too many attempts. Please wait 10 minutes.'];
    }
    $user = get_user_by_email($email);
    $hash = $user['password_hash'] ?? '';
    // Constant-ish time behaviour even when the user does not exist.
    if (!$user || !(int)$user['active'] || !password_verify($password, $hash ?: '$2y$10$invalidinvalidinvalidinvalidinvalidinva')) {
        login_attempt_record($ip);
        return ['ok' => false, 'error' => 'Invalid email or password.'];
    }
    // Rehash opportunistically if the algorithm changed.
    if (password_needs_rehash($hash, PASSWORD_DEFAULT)) {
        $pdo = cms_pdo();
        $st = $pdo->prepare("UPDATE users SET password_hash=? WHERE id=?");
        $st->execute([password_hash($password, PASSWORD_DEFAULT), $user['id']]);
    }
    session_regenerate_id(true);
    $_SESSION['uid'] = (int)$user['id'];
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    log_activity((int)$user['id'], 'login', 'Signed in from ' . $ip);
    return ['ok' => true, 'user' => $user];
}

function logout(): void {
    $u = current_user();
    if ($u) log_activity((int)$u['id'], 'logout', 'Signed out');
    $_SESSION = [];
    if (ini_get('session.use_cookies')) {
        $p = session_get_cookie_params();
        setcookie(session_name(), '', ['expires' => time() - 3600, 'path' => $p['path'], 'httponly' => true, 'samesite' => 'Lax', 'secure' => $p['secure']]);
    }
    session_destroy();
}

/** Append a row to the activity log. */
function log_activity(?int $userId, string $action, string $detail = ''): void {
    try {
        $pdo = cms_pdo();
        $st = $pdo->prepare("INSERT INTO activity_log (user_id, action, detail, ip) VALUES (?,?,?,?)");
        $st->execute([$userId, $action, mb_substr($detail, 0, 2000), client_ip()]);
    } catch (Throwable $t) {
        // Logging must never break the main action.
    }
}

function role_label(string $role): string {
    return ucwords(str_replace('_', ' ', $role));
}
