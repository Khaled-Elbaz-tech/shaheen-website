<?php
/**
 * CSRF protection. One token per session; emitted into every form,
 * verified on every POST.
 */
declare(strict_types=1);

function csrf_token(): string {
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}

/** Returns an HTML hidden input carrying the token. */
function csrf_field(): string {
    return '<input type="hidden" name="csrf_token" value="' . e(csrf_token()) . '">';
}

function csrf_verify(?string $token): bool {
    $stored = $_SESSION['csrf_token'] ?? '';
    return is_string($token) && $stored !== '' && hash_equals($stored, $token);
}

/** Abort the request with 419 when the token is missing/invalid. */
function csrf_require(): void {
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        if (!csrf_verify($_POST['csrf_token'] ?? null)) {
            http_response_code(419);
            die('Invalid or expired form token. Please go back and try again.');
        }
    }
}
