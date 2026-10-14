<?php /** SEO editor. Vars: $site, $groups, $media */ ?>
<form method="post" action="<?= admin_action('seo_save') ?>">
<?= csrf_field() ?>
<?php require __DIR__ . '/_picker.php'; ?>
<div class="card">
  <h2>Site SEO</h2>
  <div class="field"><label for="s-title">Site title</label><input type="text" id="s-title" name="seo_title" value="<?= e($site['seo']['title'] ?? '') ?>" maxlength="160"><span class="hint">Also used as the site name in Settings.</span></div>
  <div class="field"><label for="s-desc">Meta description</label><textarea id="s-desc" name="seo_description" style="min-height:80px" maxlength="320"><?= e($site['seo']['description'] ?? '') ?></textarea></div>
  <div class="field"><label>OG image (social share)</label>
    <input type="hidden" id="ogKey" name="seo_og_image" value="<?= e($site['seo']['og_image'] ?? '') ?>">
    <div style="display:flex;gap:10px;align-items:center">
      <img id="ogPrev" class="hero-preview" style="max-width:220px;<?= empty($site['seo']['og_image']) ? 'display:none' : '' ?>" src="<?= !empty($site['seo']['og_image']) ? '../dist/assets/' . e($site['seo']['og_image']) . '.webp' : '' ?>" alt="">
      <button type="button" class="btn ghost small" onclick="pickSingle('ogKey','ogPrev')">Choose…</button>
      <button type="button" class="btn ghost small" onclick="document.getElementById('ogKey').value='';document.getElementById('ogPrev').style.display='none'">Clear</button>
    </div></div>
</div>

<div class="card">
  <h2>Per-project meta</h2>
  <p class="lede">Leave empty to fall back to the project title and overview text. These fields are stored on each project and ignored by the build until the frontend reads them.</p>
  <div class="searchbar"><input type="search" placeholder="Filter projects…" data-table-filter="seoTbl" aria-label="Filter projects"></div>
  <table class="tbl" id="seoTbl">
    <thead><tr><th>Project</th><th>Meta title</th><th>Meta description</th></tr></thead>
    <tbody>
    <?php foreach ($groups as $g): ?>
      <tr>
        <td style="white-space:nowrap"><strong><?= e($g['title'] ?? '') ?></strong><br><span style="color:#6B6E68;font-size:.8rem;font-family:ui-monospace,monospace"><?= e($g['id']) ?></span></td>
        <td><input type="text" name="pmt[<?= e($g['id']) ?>]" value="<?= e($g['meta_title'] ?? '') ?>" maxlength="160" aria-label="Meta title for <?= e($g['title'] ?? '') ?>"></td>
        <td><input type="text" name="pmd[<?= e($g['id']) ?>]" value="<?= e($g['meta_description'] ?? '') ?>" maxlength="320" aria-label="Meta description for <?= e($g['title'] ?? '') ?>"></td>
      </tr>
    <?php endforeach; ?>
    </tbody>
  </table>
</div>

<div class="actions">
  <button class="btn" type="submit">Save & rebuild site</button>
  <a class="btn ghost" href="<?= admin_url('dashboard') ?>">Cancel</a>
</div>
</form>
