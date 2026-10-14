<?php
/** POST do=login — authenticate (public page, rate-limited). */
declare(strict_types=1);

$email = trim((string)($_POST['email'] ?? ''));
$password = (string)($_POST['password'] ?? '');
if ($email === '' || $password === '') {
    redirect(admin_url('login', ['err' => 'Please enter your email and password.']));
}
$res = attempt_login($email, $password);
if (!$res['ok']) {
    redirect(admin_url('login', ['err' => $res['error']]));
}
redirect(admin_url('dashboard'));
