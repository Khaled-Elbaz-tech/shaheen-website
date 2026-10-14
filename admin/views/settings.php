<?php /** Settings. Vars: $site, $build_status */ ?>
<div class="card">
  <h2>Site name</h2>
  <p class="lede">This is the browser-tab title and default SEO title (same field as SEO → Site title).</p>
  <form method="post" action="<?= admin_action('seo_save') ?>">
    <?= csrf_field() ?>
    <div class="field"><label for="set-name">Site name</label><input type="text" id="set-name" name="seo_title" value="<?= e($site['seo']['title'] ?? '') ?>" maxlength="160"></div>
    <input type="hidden" name="seo_description" value="<?= e($site['seo']['description'] ?? '') ?>">
    <input type="hidden" name="seo_og_image" value="<?= e($site['seo']['og_image'] ?? '') ?>">
    <button class="btn" type="submit">Save</button>
  </form>
</div>

<div class="card">
  <h2>Rebuild site</h2>
  <dl class="kv">
    <dt>Build script</dt><dd><code>build.py</code> <?= file_exists(BUILD_PY) ? 'found' : '<strong>missing</strong>' ?></dd>
    <dt>Python</dt><dd><code><?= e(PHP_OS_FAMILY === 'Windows' ? 'python' : 'python3') ?></code></dd>
    <dt>Draft filtering</dt><dd><?= $build_status ? 'supported by build.py' : 'not supported — drafts may still publish' ?></dd>
    <dt>content.json</dt><dd><?= is_writable(CONTENT_JSON) ? 'writable' : '<strong>not writable</strong>' ?></dd>
    <dt>site.json</dt><dd><?= file_exists(SITE_JSON) ? (is_writable(SITE_JSON) ? 'writable' : '<strong>not writable</strong>') : 'not created yet (created on first save)' ?></dd>
    <dt>assets folder</dt><dd><?= is_writable(ASSETS_DIR) ? 'writable' : '<strong>not writable</strong>' ?></dd>
  </dl>
  <form method="post" action="<?= admin_action('rebuild') ?>" style="margin-top:14px">
    <?= csrf_field() ?>
    <button class="btn" type="submit">Rebuild now</button>
  </form>
  <?php if (!empty($_SESSION['build_output'])): ?>
    <h3 style="margin-top:18px">Last build output</h3>
    <div class="build-output"><?= e($_SESSION['build_output']) ?></div>
    <?php unset($_SESSION['build_output']); ?>
  <?php endif; ?>
</div>

<div class="danger-zone">
  <h3>Danger zone</h3>
  <p style="color:#6B6E68;font-size:.9rem">There is no server cache to clear — the site is static. The only destructive option here is the activity log.</p>
  <form method="post" action="<?= admin_action('settings_save') ?>">
    <?= csrf_field() ?><input type="hidden" name="sub" value="clear_log">
    <button class="btn danger" type="submit" data-confirm="Delete all activity log entries? This cannot be undone.">Clear activity log</button>
  </form>
</div>
