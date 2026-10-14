<?php /** Media library. Vars: $media */ ?>
<div class="card">
  <h2>Upload</h2>
  <p class="lede">JPG, PNG or WebP · up to 10 MB · converted to WebP and downscaled to 2200px wide when GD is available.<?= extension_loaded('gd') ? '' : ' <strong>GD is not loaded on this server — originals are stored as-is.</strong>' ?></p>
  <form method="post" action="<?= admin_action('media_upload') ?>" enctype="multipart/form-data">
    <?= csrf_field() ?>
    <div class="row">
      <div class="field"><label for="up-file">Image file</label><input type="file" id="up-file" name="image" accept=".jpg,.jpeg,.png,.webp" required></div>
      <div class="field"><label for="up-title">Title (optional)</label><input type="text" id="up-title" name="title" maxlength="200"></div>
    </div>
    <div class="field"><label for="up-alt">Alt text (optional)</label><input type="text" id="up-alt" name="alt" maxlength="200"></div>
    <button class="btn" type="submit">Upload</button>
  </form>
</div>

<div class="toolbar">
  <div class="searchbar" style="margin:0">
    <input type="search" id="mq" placeholder="Search filename…" aria-label="Search media">
  </div>
  <span style="color:#6B6E68;font-size:.88rem"><?= count($media) ?> assets</span>
</div>

<div class="media-grid" id="mediaGrid">
<?php foreach ($media as $m):
  $uses = media_usage($m['key']);
?>
  <div class="media-card" data-key="<?= e($m['key']) ?>">
    <img src="../dist/assets/<?= e($m['key']) ?>.webp" alt="<?= e($m['alt'] ?: $m['title']) ?>" loading="lazy">
    <div class="media-meta">
      <div class="key"><?= e($m['key']) ?></div>
      <?php if ($m['title']): ?><div><?= e(trunc($m['title'], 40)) ?></div><?php endif; ?>
      <div class="dim"><?= $m['width'] ? e((string)$m['width']) . '×' . e((string)$m['height']) . ' · ' : '' ?><?= e(human_filesize((int)$m['bytes'])) ?><?= $uses ? ' · <strong style="color:#9A6B1E">in use (' . count($uses) . ')</strong>' : '' ?></div>
    </div>
    <div class="media-tools">
      <details style="width:100%">
        <summary style="cursor:pointer;font-size:.84rem;color:#4F5344">Edit title / alt / caption</summary>
        <form method="post" action="<?= admin_action('media_meta') ?>" style="margin-top:8px">
          <?= csrf_field() ?><input type="hidden" name="key" value="<?= e($m['key']) ?>">
          <div class="field"><label>Title</label><input type="text" name="title" value="<?= e($m['title']) ?>" maxlength="200"></div>
          <div class="field"><label>Alt text</label><input type="text" name="alt" value="<?= e($m['alt']) ?>" maxlength="200"></div>
          <div class="field"><label>Caption</label><input type="text" name="caption" value="<?= e($m['caption']) ?>" maxlength="200"></div>
          <button class="btn small" type="submit">Save</button>
        </form>
      </details>
      <form method="post" action="<?= admin_action('media_delete') ?>" class="inline-form" style="width:100%">
        <?= csrf_field() ?><input type="hidden" name="key" value="<?= e($m['key']) ?>">
        <?php if ($uses): ?>
          <label style="font-size:.8rem;display:block;margin:6px 0"><input type="checkbox" name="force" value="1"> delete anyway — used in: <?= e(implode('; ', array_slice($uses, 0, 3))) ?></label>
        <?php endif; ?>
        <button class="btn small danger" type="submit" data-confirm="Delete <?= e($m['key']) ?>?<?= $uses ? ' It is referenced in content — pages will break.' : '' ?>">Delete</button>
      </form>
    </div>
  </div>
<?php endforeach; ?>
</div>

<script>
document.getElementById('mq').addEventListener('input', function () {
  var q = this.value.toLowerCase();
  document.querySelectorAll('#mediaGrid .media-card').forEach(function (c) {
    c.style.display = c.getAttribute('data-key').toLowerCase().indexOf(q) === -1 ? 'none' : '';
  });
});
</script>
