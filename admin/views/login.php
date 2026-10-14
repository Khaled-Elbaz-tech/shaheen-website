<?php /** Standalone login page. */ ?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>Sign in · Ola Magdy CMS</title>
<link rel="stylesheet" href="assets/admin.css?v=1">
</head>
<body>
<div class="login-wrap">
  <div class="login-card">
    <h1>ola magdy<span style="color:#B89B5E">.</span></h1>
    <p class="lede">Portfolio CMS — sign in to manage projects, pages and media.</p>
    <?php if (!empty($_GET['err'])): ?><div class="flash error"><?= e($_GET['err']) ?></div><?php endif; ?>
    <?php foreach (flashes() as $f): ?><div class="flash <?= e($f['type']) ?>"><?= e($f['message']) ?></div><?php endforeach; ?>
    <form method="post" action="<?= admin_action('login') ?>">
      <?= csrf_field() ?>
      <div class="field"><label for="email">Email</label><input type="email" id="email" name="email" required autocomplete="username" autofocus></div>
      <div class="field"><label for="password">Password</label><input type="password" id="password" name="password" required autocomplete="current-password"></div>
      <button class="btn" type="submit" style="width:100%;justify-content:center">Sign in</button>
    </form>
    <p style="margin-top:18px"><a href="../dist/index.html">← Back to website</a></p>
  </div>
</div>
</body>
</html>
