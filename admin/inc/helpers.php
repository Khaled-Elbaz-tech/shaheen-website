<?php
/**
 * Small helpers shared by every page: escaping, flash messages,
 * redirects, URL builders, date formatting.
 */
declare(strict_types=1);

/* PHP 8.0 compat: array_is_list() exists since 8.1. */
if (!function_exists('array_is_list')) {
    function array_is_list(array $a): bool {
        $i = 0;
        foreach ($a as $k => $v) { if ($k !== $i++) return false; }
        return true;
    }
}

/* mbstring is standard on XAMPP and most hosts; fall back gracefully if missing. */
if (!function_exists('mb_strlen')) {
    function mb_strlen($s, $enc = null) { return strlen((string)$s); }
    function mb_substr($s, $start, $len = null, $enc = null) {
        return $len === null ? substr((string)$s, $start) : substr((string)$s, $start, $len);
    }
}

function e(?string $v): string {
    return htmlspecialchars((string)$v, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/** Admin URL builder: admin_url('projects', ['id'=>'x']) -> index.php?page=projects&id=x */
function admin_url(string $page = 'dashboard', array $params = []): string {
    $q = array_merge(['page' => $page], $params);
    return 'index.php?' . http_build_query($q, '', '&', PHP_QUERY_RFC3986);
}

/** Action endpoint: admin_action('project_save') -> index.php?do=project_save */
function admin_action(string $do, array $params = []): string {
    $q = array_merge(['do' => $do], $params);
    return 'index.php?' . http_build_query($q, '', '&', PHP_QUERY_RFC3986);
}

function redirect(string $url): void {
    header('Location: ' . $url);
    exit;
}

/** POST-redirect-GET with a one-time flash message. */
function redirect_back(string $fallback = 'index.php?page=dashboard'): void {
    $to = $_POST['redirect_to'] ?? $_GET['redirect_to'] ?? $fallback;
    // Only allow internal relative URLs to prevent open redirects.
    if (!is_string($to) || $to === '' || preg_match('#^(https?:)?//#i', $to) || str_starts_with($to, 'javascript:')) {
        $to = $fallback;
    }
    redirect($to);
}

function flash(string $type, string $message): void {
    $_SESSION['flash'][] = ['type' => $type, 'message' => $message];
}

/** Returns and clears queued flash messages. */
function flashes(): array {
    $f = $_SESSION['flash'] ?? [];
    unset($_SESSION['flash']);
    return $f;
}

function client_ip(): string {
    foreach (['HTTP_X_FORWARDED_FOR', 'HTTP_CLIENT_IP', 'REMOTE_ADDR'] as $k) {
        if (!empty($_SERVER[$k])) {
            $ip = explode(',', (string)$_SERVER[$k])[0];
            return trim($ip);
        }
    }
    return 'unknown';
}

function fmt_dt(?string $dt): string {
    if (!$dt) return '—';
    $t = strtotime($dt);
    return $t ? date('M j, Y · H:i', $t) : e($dt);
}

function human_filesize(int $bytes): string {
    if ($bytes < 1024) return $bytes . ' B';
    $units = ['KB', 'MB', 'GB'];
    $i = 0; $v = $bytes / 1024;
    while ($v >= 1024 && $i < 2) { $v /= 1024; $i++; }
    return round($v, 1) . ' ' . $units[$i];
}

/** Truncate text without cutting a multibyte char. */
function trunc(?string $s, int $len = 90): string {
    $s = (string)$s;
    if (mb_strlen($s) <= $len) return $s;
    return mb_substr($s, 0, $len - 1) . '…';
}

/** Validate a nav/asset URL: relative paths and http(s) allowed, javascript:/data: blocked. */
function is_safe_url(string $url): bool {
    $url = trim($url);
    if ($url === '') return false;
    if (preg_match('#^\s*(javascript|data|vbscript):#i', $url)) return false;
    if (str_starts_with($url, '#') || str_starts_with($url, '/') || str_starts_with($url, './')) return true;
    if (filter_var($url, FILTER_VALIDATE_URL)) {
        return (bool)preg_match('#^https?://#i', $url);
    }
    // Plain relative like "projects/x/" or "index.html"
    return (bool)preg_match('#^[A-Za-z0-9._~%!$&\'()*+,;=:@/-]+$#', $url);
}

/** Validate a slug/id: lowercase letters, digits, hyphens. */
function is_valid_slug(string $slug): bool {
    return (bool)preg_match('#^[a-z0-9][a-z0-9-]{1,80}$#', $slug);
}

/** Sanitise an uploaded filename: strip path, spaces, weird chars. */
function safe_filename(string $name): string {
    $name = basename($name);
    $name = preg_replace('#[^\w\-.]+#u', '-', $name);
    $name = trim($name, '-.');
    if ($name === '' || $name === '.' || $name === '..') $name = 'upload';
    return mb_substr($name, 0, 120);
}
