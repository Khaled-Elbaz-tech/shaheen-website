<?php /** First-run setup: create the super_admin account. Shown only when users table is empty. */ ?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>First-run setup · Ola Magdy CMS</title>
<link rel="stylesheet" href="assets/admin.css?v=1">
</head>
<body>
<div class="login-wrap">
  <div class="login-card">
    <h1>Welcome<span style="color:#B89B5E">.</span></h1>
    <p class="lede">This CMS has no users yet. Create your <strong>super admin</strong> account — it has full access and manages all other users. There are no default credentials.</p>
    <?php foreach (flashes() as $f): ?><div class="flash <?= e($f['type']) ?>"><?= e($f['message']) ?></div><?php endforeach; ?>
    <form method="post" action="<?= admin_action('setup') ?>">
      <?= csrf_field() ?>
      <div class="field"><label for="name">Full name</label><input type="text" id="name" name="name" required maxlength="120" autocomplete="name" autofocus></div>
      <div class="field"><label for="email">Email</label><input type="email" id="email" name="email" required maxlength="180" autocomplete="email"></div>
      <div class="field"><label for="pw1">Password <span class="hint">Minimum 10 characters.</span></label><input type="password" id="pw1" name="password" required minlength="10" autocomplete="new-password"></div>
      <div class="field"><label for="pw2">Confirm password</label><input type="password" id="pw2" name="password2" required minlength="10" autocomplete="new-password"></div>
      <button class="btn" type="submit" style="width:100%;justify-content:center">Create super admin</button>
    </form>
  </div>
</div>
</body>
</html>
