<?php
/** App shell: sidebar + topbar. Expects $content, $title, $user, $page. */
$page = $page ?? ($_GET['page'] ?? 'dashboard');
$nav_items = [
    ['dashboard', 'Dashboard', '⊞', 'activity'],
    ['projects', 'Projects', '◧', 'projects'],
    ['pages', 'Pages & Sections', '▤', 'pages'],
    ['media', 'Media', '◫', 'media'],
    ['journal', 'Journal', '✎', 'journal'],
    ['nav', 'Navigation', '☰', 'nav'],
    ['seo', 'SEO', '◎', 'seo'],
    ['inquiries', 'Inquiries', '✉', 'inquiries'],
    ['users', 'Users', '◉', 'users'],
    ['settings', 'Settings', '⚙', 'settings'],
    ['activity', 'Activity Log', '◔', 'activity'],
];
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<title><?= e($title ?? 'Admin') ?> · Ola Magdy CMS</title>
<link rel="stylesheet" href="assets/admin.css?v=1">
<script src="assets/admin.js?v=1" defer></script>
</head>
<body>
<div class="app">
  <button class="sidebar-toggle" id="sidebarToggle" aria-label="Toggle navigation" aria-expanded="false">☰</button>
  <aside class="sidebar" id="sidebar">
    <div class="brand"><span class="brand-mark">om.</span><span class="brand-sub">Portfolio CMS</span></div>
    <nav class="sidenav" aria-label="Admin">
      <?php foreach ($nav_items as [$slug, $label, $icon, $perm]): ?>
        <?php if (!can($perm)) continue; ?>
        <a href="<?= admin_url($slug) ?>" class="navlink<?= $page === $slug ? ' active' : '' ?>">
          <span class="navicon" aria-hidden="true"><?= $icon ?></span><?= e($label) ?>
          <?php if ($slug === 'inquiries' && ($GLOBALS['__unread'] ?? 0) > 0): ?>
            <span class="badge"><?= (int)$GLOBALS['__unread'] ?></span>
          <?php endif; ?>
        </a>
      <?php endforeach; ?>
    </nav>
    <div class="side-foot">
      <div class="side-user">
        <span class="avatar"><?= e(mb_substr($user['name'] ?? '?', 0, 1)) ?></span>
        <span class="side-user-meta"><strong><?= e($user['name'] ?? '') ?></strong><em><?= e(role_label($user['role'] ?? 'viewer')) ?></em></span>
      </div>
    </div>
  </aside>
  <div class="main">
    <header class="topbar">
      <h1><?= e($title ?? '') ?></h1>
      <div class="topbar-actions">
        <a class="btn ghost" href="../dist/index.html" target="_blank" rel="noopener">View website ↗</a>
        <a class="btn ghost" href="<?= admin_url('logout') ?>">Log out</a>
      </div>
    </header>
    <main class="content">
      <?php foreach (flashes() as $f): ?>
        <div class="flash <?= e($f['type']) ?>" role="status"><?= e($f['message']) ?></div>
      <?php endforeach; ?>
      <?php if (isset($_GET['rebuilt'])): ?>
        <div class="flash success" role="status">Site rebuilt successfully.</div>
      <?php endif; ?>
      <?= $content ?>
    </main>
    <footer class="pagefoot">Ola Magdy · Portfolio CMS — changes rebuild the static site automatically.</footer>
  </div>
</div>
<div class="scrim" id="scrim"></div>
</body>
</html>
