<?php /** Pages & sections editor (site.json). Vars: $site, $media, $build_disabled */
$sections = site_sections_editor($site);
?>
<?php if (!$build_disabled): ?>
<div class="flash warn">Section disabling is not yet supported by <code>build.py</code> — it renders every section in the order list. Disabled sections are stored and will take effect once the build honours them.</div>
<?php endif; ?>
<form method="post" action="<?= admin_action('pages_save') ?>">
<?= csrf_field() ?>
<?php require __DIR__ . '/_picker.php'; ?>

<div data-tabs>
  <div class="tabs" role="tablist">
    <button type="button" class="tab-btn active" data-tab="t-hero" aria-selected="true">Hero</button>
    <button type="button" class="tab-btn" data-tab="t-intro" aria-selected="false">Intro</button>
    <button type="button" class="tab-btn" data-tab="t-sections" aria-selected="false">Sections</button>
    <button type="button" class="tab-btn" data-tab="t-studio" aria-selected="false">Studio</button>
    <button type="button" class="tab-btn" data-tab="t-approach" aria-selected="false">Approach</button>
    <button type="button" class="tab-btn" data-tab="t-landscape" aria-selected="false">Landscape</button>
    <button type="button" class="tab-btn" data-tab="t-contact" aria-selected="false">Contact</button>
  </div>

  <div class="tab-panel active" id="t-hero"><div class="card">
    <h2>Hero</h2>
    <div class="field"><label for="h-head">Headline</label><input type="text" id="h-head" name="hero_headline" value="<?= e($site['hero']['headline'] ?? '') ?>" maxlength="200"></div>
    <div class="field"><label for="h-desc">Descriptor</label><textarea id="h-desc" name="hero_descriptor"><?= e($site['hero']['descriptor'] ?? '') ?></textarea></div>
    <div class="row">
      <div class="field"><label for="h-pid">Linked project (slug, optional)</label><input type="text" id="h-pid" name="hero_project_id" value="<?= e($site['hero']['project_id'] ?? '') ?>" placeholder="e.g. umiam-lake"><span class="hint">Must match a project slug from the Projects list.</span></div>
      <div class="field"><label for="h-alt">Image alt text</label><input type="text" id="h-alt" name="hero_alt" value="<?= e($site['hero']['alt'] ?? '') ?>" maxlength="200"></div>
    </div>
    <div class="field"><label>Hero image</label>
      <input type="hidden" id="heroImgKey" name="hero_image" value="<?= e($site['hero']['image'] ?? '') ?>">
      <div style="display:flex;gap:10px;align-items:center">
        <img id="heroImgPrev" class="hero-preview" style="max-width:220px;<?= empty($site['hero']['image']) ? 'display:none' : '' ?>" src="<?= !empty($site['hero']['image']) ? '../dist/assets/' . e($site['hero']['image']) . '.webp' : '' ?>" alt="">
        <button type="button" class="btn ghost small" onclick="pickSingle('heroImgKey','heroImgPrev')">Choose…</button>
      </div></div>
  </div></div>

  <div class="tab-panel" id="t-intro"><div class="card">
    <h2>Intro</h2>
    <div class="field"><label for="i-eyebrow">Eyebrow</label><input type="text" id="i-eyebrow" name="intro_eyebrow" value="<?= e($site['intro']['eyebrow'] ?? '') ?>" maxlength="200"></div>
    <div class="field"><label for="i-stmt">Statement</label><input type="text" id="i-stmt" name="intro_statement" value="<?= e($site['intro']['statement'] ?? '') ?>" maxlength="200"></div>
    <div class="field"><label for="i-copy">Copy</label><textarea id="i-copy" name="intro_copy"><?= e($site['intro']['copy'] ?? '') ?></textarea></div>
  </div></div>

  <div class="tab-panel" id="t-sections"><div class="card">
    <h2>Sections</h2>
    <p class="lede">Reorder homepage sections with ↑ ↓. Unchecked sections are stored as disabled<?= $build_disabled ? '' : ' (not yet honoured by the build — see warning above)' ?>.</p>
    <table class="tbl"><thead><tr><th></th><th>Section</th><th>Enabled</th><th>Order</th></tr></thead><tbody id="secRows">
      <?php foreach ($sections as $s): ?>
      <tr>
        <td><input type="hidden" name="section_id[]" value="<?= e($s['id']) ?>"></td>
        <td><strong><?= e($s['label']) ?></strong> <span style="color:#6B6E68;font-size:.82rem"><?= e($s['id']) ?></span></td>
        <td><label><input type="checkbox" name="section_enabled[<?= e($s['id']) ?>]" value="1"<?= $s['enabled'] ? ' checked' : '' ?>> show</label></td>
        <td style="white-space:nowrap"><button type="button" class="btn small ghost" onclick="moveRow(this,-1)" aria-label="Move up">↑</button> <button type="button" class="btn small ghost" onclick="moveRow(this,1)" aria-label="Move down">↓</button></td>
      </tr>
      <?php endforeach; ?>
    </tbody></table>
  </div></div>

  <div class="tab-panel" id="t-studio"><div class="card">
    <h2>Studio</h2>
    <div class="field"><label for="s-head">Headline</label><input type="text" id="s-head" name="studio_headline" value="<?= e($site['studio']['headline'] ?? '') ?>" maxlength="200"></div>
    <div class="field"><label for="s-intro">Intro</label><textarea id="s-intro" name="studio_intro"><?= e($site['studio']['intro'] ?? '') ?></textarea></div>
    <div class="field"><label for="s-bio">Bio</label><textarea id="s-bio" name="studio_bio" style="min-height:150px"><?= e($site['studio']['bio'] ?? '') ?></textarea></div>
    <div class="field"><label for="s-phil">Philosophy</label><textarea id="s-phil" name="studio_philosophy"><?= e($site['studio']['philosophy'] ?? '') ?></textarea></div>
    <div class="field"><label>Studio image</label>
      <input type="hidden" id="studioImgKey" name="studio_image" value="<?= e($site['studio']['image'] ?? '') ?>">
      <div style="display:flex;gap:10px;align-items:center">
        <img id="studioImgPrev" class="hero-preview" style="max-width:220px;<?= empty($site['studio']['image']) ? 'display:none' : '' ?>" src="<?= !empty($site['studio']['image']) ? '../dist/assets/' . e($site['studio']['image']) . '.webp' : '' ?>" alt="">
        <button type="button" class="btn ghost small" onclick="pickSingle('studioImgKey','studioImgPrev')">Choose…</button>
      </div></div>
    <div class="row">
      <div class="field"><label for="s-alt">Image alt text</label><input type="text" id="s-alt" name="studio_image_alt" value="<?= e($site['studio']['image_alt'] ?? '') ?>" maxlength="200"></div>
      <div class="field"><label for="s-cap">Image caption</label><input type="text" id="s-cap" name="studio_image_caption" value="<?= e($site['studio']['image_caption'] ?? '') ?>" maxlength="200"></div>
    </div>
  </div></div>

  <div class="tab-panel" id="t-approach"><div class="card">
    <h2>Approach</h2>
    <div class="field"><label for="a-head">Headline</label><input type="text" id="a-head" name="approach_headline" value="<?= e($site['approach']['headline'] ?? '') ?>" maxlength="200"></div>
    <div class="field"><label for="a-intro">Intro</label><textarea id="a-intro" name="approach_intro"><?= e($site['approach']['intro'] ?? '') ?></textarea></div>
    <?php $stages = $site['approach']['stages'] ?? []; for ($i = 0; $i < 4; $i++): $sg = $stages[$i] ?? ['title' => '', 'text' => '']; ?>
    <div class="slide"><div class="slide-head"><h3>Stage <?= str_pad((string)($i + 1), 2, '0', STR_PAD_LEFT) ?></h3></div>
      <div class="field"><label>Title</label><input type="text" name="stage_title_<?= $i ?>" value="<?= e($sg['title'] ?? '') ?>" maxlength="120"></div>
      <div class="field"><label>Text</label><textarea name="stage_text_<?= $i ?>"><?= e($sg['text'] ?? '') ?></textarea></div>
    </div>
    <?php endfor; ?>
  </div></div>

  <div class="tab-panel" id="t-landscape"><div class="card">
    <h2>Landscape gallery</h2>
    <div class="field"><label for="l-head">Headline</label><input type="text" id="l-head" name="lg_headline" value="<?= e($site['landscape_gallery']['headline'] ?? '') ?>" maxlength="200"></div>
    <div class="field"><label for="l-intro">Intro</label><textarea id="l-intro" name="lg_intro"><?= e($site['landscape_gallery']['intro'] ?? '') ?></textarea></div>
    <div id="lgRows">
      <?php foreach (($site['landscape_gallery']['images'] ?? []) as $i => $im): ?>
      <div class="row" data-lgrow style="align-items:end">
        <div class="field"><label>Image key</label><input type="text" name="lg_images[<?= $i ?>][key]" value="<?= e($im['key'] ?? '') ?>"></div>
        <div class="field"><label>Caption</label><input type="text" name="lg_images[<?= $i ?>][caption]" value="<?= e($im['caption'] ?? '') ?>" maxlength="200"></div>
        <div class="field"><label>Alt</label><input type="text" name="lg_images[<?= $i ?>][alt]" value="<?= e($im['alt'] ?? '') ?>" maxlength="200"></div>
        <div class="field"><button type="button" class="btn small danger" onclick="this.closest('[data-lgrow]').remove()">Remove</button></div>
      </div>
      <?php endforeach; ?>
    </div>
    <button type="button" class="btn ghost small" onclick="addLgRow()">+ Add image</button>
  </div></div>

  <div class="tab-panel" id="t-contact"><div class="card">
    <h2>Contact</h2>
    <div class="field"><label for="c-head">Headline</label><input type="text" id="c-head" name="contact_headline" value="<?= e($site['contact']['headline'] ?? '') ?>" maxlength="200"></div>
    <div class="field"><label for="c-copy">Copy</label><textarea id="c-copy" name="contact_copy"><?= e($site['contact']['copy'] ?? '') ?></textarea></div>
    <div class="field"><label for="c-email">Email</label><input type="email" id="c-email" name="contact_email" value="<?= e($site['contact']['email'] ?? '') ?>" maxlength="180"></div>
    <h3>Social links</h3>
    <div id="socRows">
      <?php $si = 0; foreach (($site['contact']['socials'] ?? []) as $lbl => $url): ?>
      <div class="row" data-socrow style="align-items:end">
        <div class="field"><label>Label</label><input type="text" name="social_label[<?= $si ?>]" value="<?= e($lbl) ?>" maxlength="60"></div>
        <div class="field"><label>URL</label><input type="url" name="social_url[<?= $si ?>]" value="<?= e($url) ?>" maxlength="300"></div>
        <div class="field"><button type="button" class="btn small danger" onclick="this.closest('[data-socrow]').remove()">Remove</button></div>
      </div>
      <?php $si++; endforeach; ?>
    </div>
    <button type="button" class="btn ghost small" onclick="addSocRow()">+ Add social link</button>
  </div></div>
</div>

<div class="actions" style="position:sticky;bottom:0;background:var(--ivory);padding:14px 0">
  <button class="btn" type="submit">Save & rebuild site</button>
  <a class="btn ghost" href="<?= admin_url('dashboard') ?>">Cancel</a>
</div>
</form>

<script>
function moveRow(btn, dir) {
  var tr = btn.closest('tr'), sib = dir < 0 ? tr.previousElementSibling : tr.nextElementSibling;
  if (sib) { dir < 0 ? tr.parentNode.insertBefore(tr, sib) : tr.parentNode.insertBefore(sib, tr); }
}
var lgIdx = <?= count($site['landscape_gallery']['images'] ?? []) ?>;
function addLgRow() {
  var d = document.createElement('div'); d.className = 'row'; d.setAttribute('data-lgrow', ''); d.style.alignItems = 'end';
  d.innerHTML = '<div class="field"><label>Image key</label><input type="text" name="lg_images[' + lgIdx + '][key]"></div>' +
    '<div class="field"><label>Caption</label><input type="text" name="lg_images[' + lgIdx + '][caption]" maxlength="200"></div>' +
    '<div class="field"><label>Alt</label><input type="text" name="lg_images[' + lgIdx + '][alt]" maxlength="200"></div>' +
    '<div class="field"><button type="button" class="btn small danger" onclick="this.closest(\'[data-lgrow]\').remove()">Remove</button></div>';
  lgIdx++; document.getElementById('lgRows').appendChild(d);
}
var socIdx = <?= $si ?? 0 ?>;
function addSocRow() {
  var d = document.createElement('div'); d.className = 'row'; d.setAttribute('data-socrow', ''); d.style.alignItems = 'end';
  d.innerHTML = '<div class="field"><label>Label</label><input type="text" name="social_label[' + socIdx + ']" maxlength="60"></div>' +
    '<div class="field"><label>URL</label><input type="url" name="social_url[' + socIdx + ']" maxlength="300"></div>' +
    '<div class="field"><button type="button" class="btn small danger" onclick="this.closest(\'[data-socrow]\').remove()">Remove</button></div>';
  socIdx++; document.getElementById('socRows').appendChild(d);
}
</script>
