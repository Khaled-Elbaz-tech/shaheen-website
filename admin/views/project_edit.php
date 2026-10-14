<?php
/** Project editor. Vars: $group (null=new), $all, $media, $revisions, $number_default, $build_status, $user */
$g = $group;
$isNew = $g === null;
$st = $isNew ? 'published' : project_status($g);
$cats = [];
foreach ($all as $a) { if (!empty($a['category'])) $cats[$a['category']] = true; }
$cats = array_keys($cats); sort($cats);
?>
<?php if (!$build_status): ?>
<div class="flash warn">The current <code>build.py</code> does not filter by status — drafts/archived projects may still appear on the public site until the build is updated.</div>
<?php endif; ?>

<form method="post" action="<?= admin_action('project_save') ?>">
<?= csrf_field() ?>
<?php if (!$isNew): ?><input type="hidden" name="id" value="<?= e($g['id']) ?>"><?php endif; ?>

<div data-tabs>
  <div class="tabs" role="tablist">
    <button type="button" class="tab-btn active" data-tab="tab-overview" aria-selected="true">Overview</button>
    <button type="button" class="tab-btn" data-tab="tab-details" aria-selected="false">Details</button>
    <button type="button" class="tab-btn" data-tab="tab-gallery" aria-selected="false">Gallery <span class="pill published" style="font-size:.68rem"><?= $isNew ? 0 : count($g['slides'] ?? []) ?></span></button>
    <button type="button" class="tab-btn" data-tab="tab-seo" aria-selected="false">SEO</button>
    <button type="button" class="tab-btn" data-tab="tab-pub" aria-selected="false">Publishing</button>
  </div>

  <!-- OVERVIEW -->
  <div class="tab-panel active" id="tab-overview">
    <div class="card">
      <div class="field"><label for="f-title">Title</label><input type="text" id="f-title" name="title" value="<?= e($g['title'] ?? '') ?>" required maxlength="200"></div>
      <div class="row">
        <div class="field">
          <label for="f-slug">URL slug<?= $isNew ? '' : ' (fixed)' ?></label>
          <?php if ($isNew): ?>
            <input type="text" id="f-slug" name="slug" placeholder="auto-generated from title" pattern="[a-z0-9][a-z0-9-]{1,80}">
            <span class="hint">Lowercase letters, digits, hyphens. This becomes the project page URL.</span>
          <?php else: ?>
            <input type="text" value="<?= e($g['id']) ?>" disabled><span class="hint">The slug is the project ID — it cannot change after creation.</span>
          <?php endif; ?>
        </div>
        <div class="field"><label for="f-number">Featured order #</label><input type="number" id="f-number" name="number" min="1" value="<?= e((string)($g['number'] ?? $number_default)) ?>"><span class="hint">Controls the display number and sort order.</span></div>
      </div>
      <div class="row">
        <div class="field"><label for="f-location">Location</label><input type="text" id="f-location" name="location" value="<?= e($g['location'] ?? '') ?>" required maxlength="200"></div>
        <div class="field"><label for="f-category">Category</label><input type="text" id="f-category" name="category" list="catlist" value="<?= e($g['category'] ?? '') ?>" required maxlength="120">
          <datalist id="catlist"><?php foreach ($cats as $c): ?><option value="<?= e($c) ?>"><?php endforeach; ?></datalist></div>
      </div>
      <div class="field"><label for="f-status">Status</label>
        <select id="f-status" name="status">
          <?php foreach (['published' => 'Published', 'draft' => 'Draft', 'archived' => 'Archived'] as $v => $l): ?>
            <option value="<?= $v ?>"<?= $st === $v ? ' selected' : '' ?>><?= $l ?></option>
          <?php endforeach; ?>
        </select>
        <?php if ($user['role'] === 'author'): ?><span class="hint">Authors cannot archive projects.</span><?php endif; ?>
      </div>
    </div>
  </div>

  <!-- DETAILS -->
  <div class="tab-panel" id="tab-details">
    <div class="card">
      <div class="field"><label for="f-body">Overview text</label><textarea id="f-body" name="body" style="min-height:160px"><?= e($g['body'] ?? '') ?></textarea></div>
      <div class="field">
        <label>Hero image</label>
        <input type="hidden" id="heroKey" name="hero" value="<?= e($g['hero'] ?? '') ?>">
        <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
          <img id="heroPrev" class="hero-preview" style="max-width:280px;<?= empty($g['hero']) ? 'display:none' : '' ?>" src="<?= !empty($g['hero']) ? '../dist/assets/' . e($g['hero']) . '.webp' : '' ?>" alt="Hero preview">
          <button type="button" class="btn ghost" onclick="pickSingle('heroKey','heroPrev')">Choose from media…</button>
          <button type="button" class="btn ghost small" onclick="document.getElementById('heroKey').value='';document.getElementById('heroPrev').style.display='none'">Clear</button>
        </div>
      </div>
    </div>
  </div>

  <!-- GALLERY -->
  <div class="tab-panel" id="tab-gallery">
    <div class="card">
      <div id="slidesWrap">
        <?php foreach (($g['slides'] ?? []) as $i => $s):
          $caps = $s['captions'] ?? '';
          if (!is_string($caps)) $caps = implode("\n", (array)$caps);
        ?>
        <div class="slide" data-slide="<?= $i ?>">
          <div class="slide-head"><h3>Chapter <?= $i + 1 ?></h3>
            <button type="button" class="btn small danger" onclick="removeSlide(this)">Remove</button></div>
          <div class="row">
            <div class="field"><label>Chapter title</label><input type="text" name="slides[<?= $i ?>][title]" value="<?= e($s['title'] ?? '') ?>" maxlength="200"></div>
            <div class="field"><label>Layout</label>
              <select name="slides[<?= $i ?>][layout]">
                <?php foreach (['single' => 'Single', 'pair' => 'Pair', 'stack' => 'Stack'] as $v => $l): ?>
                  <option value="<?= $v ?>"<?= ($s['layout'] ?? 'single') === $v ? ' selected' : '' ?>><?= $l ?></option>
                <?php endforeach; ?>
              </select></div>
          </div>
          <div class="field"><label>Chapter text</label><textarea name="slides[<?= $i ?>][body]"><?= e($s['body'] ?? '') ?></textarea></div>
          <div class="field"><label>Images <span class="hint">Captions: one per line, in the same order as the images.</span></label>
            <div class="slide-images">
              <?php foreach (($s['images'] ?? []) as $k): ?>
                <span class="img-chip"><input type="hidden" name="slides[<?= $i ?>][images][]" value="<?= e($k) ?>"><?= e($k) ?> <button type="button" onclick="this.parentElement.remove()" aria-label="Remove">×</button></span>
              <?php endforeach; ?>
            </div>
            <div style="margin-top:8px"><button type="button" class="btn small ghost" onclick="pickSlideImages(this)">+ Add images…</button></div>
          </div>
          <div class="field"><label>Captions (one per line)</label><textarea name="slides[<?= $i ?>][captions]" style="min-height:70px"><?= e($caps) ?></textarea></div>
          <input type="hidden" name="slides[<?= $i ?>][anchor]" value="<?= e($s['anchor'] ?? '') ?>">
        </div>
        <?php endforeach; ?>
      </div>
      <button type="button" class="btn ghost" onclick="addSlide()">+ Add chapter</button>
    </div>
  </div>

  <!-- SEO -->
  <div class="tab-panel" id="tab-seo">
    <div class="card">
      <div class="field"><label for="f-mt">Meta title</label><input type="text" id="f-mt" name="meta_title" value="<?= e($g['meta_title'] ?? '') ?>" maxlength="160"><span class="hint">Leave empty to use the project title.</span></div>
      <div class="field"><label for="f-md">Meta description</label><textarea id="f-md" name="meta_description" style="min-height:80px" maxlength="320"><?= e($g['meta_description'] ?? '') ?></textarea><span class="hint">Leave empty to use the overview text.</span></div>
    </div>
  </div>

  <!-- PUBLISHING -->
  <div class="tab-panel" id="tab-pub">
    <div class="card">
      <h2>Publish</h2>
      <p class="lede">Saving writes <code>content.json</code> and rebuilds the static site automatically.</p>
      <div class="actions">
        <button class="btn" type="submit" name="status_btn" value="published">Save & publish</button>
        <button class="btn ghost" type="submit" name="status_btn" value="draft">Save as draft</button>
        <?php if ($user['role'] !== 'author'): ?>
          <button class="btn warn" type="submit" name="status_btn" value="archived" data-confirm="Archive this project? It will be hidden from listings once the build supports status filtering.">Archive</button>
        <?php endif; ?>
        <a class="btn ghost" href="<?= admin_url('projects') ?>">Cancel</a>
      </div>
    </div>
    <?php if (!$isNew && $revisions): ?>
    <div class="card">
      <h2>Revision history</h2>
      <p class="lede">The last <?= count($revisions) ?> saved versions. <a href="<?= admin_url('revisions', ['id' => $g['id']]) ?>">View all & restore →</a></p>
    </div>
    <?php endif; ?>
  </div>
</div>
</form>

<!-- template for new chapters -->
<template id="slideTemplate">
  <div class="slide-head"><h3>Chapter</h3><button type="button" class="btn small danger" onclick="removeSlide(this)">Remove</button></div>
  <div class="row">
    <div class="field"><label>Chapter title</label><input type="text" name="slides[__IDX__][title]" maxlength="200"></div>
    <div class="field"><label>Layout</label><select name="slides[__IDX__][layout]"><option value="single">Single</option><option value="pair">Pair</option><option value="stack">Stack</option></select></div>
  </div>
  <div class="field"><label>Chapter text</label><textarea name="slides[__IDX__][body]"></textarea></div>
  <div class="field"><label>Images <span class="hint">Captions: one per line, in the same order as the images.</span></label>
    <div class="slide-images"></div>
    <div style="margin-top:8px"><button type="button" class="btn small ghost" onclick="pickSlideImages(this)">+ Add images…</button></div>
  </div>
  <div class="field"><label>Captions (one per line)</label><textarea name="slides[__IDX__][captions]" style="min-height:70px"></textarea></div>
  <input type="hidden" name="slides[__IDX__][anchor]" value="">
</template>

<?php require __DIR__ . '/_picker.php'; ?>

<?php if (!$isNew && can('projects_delete')): ?>
<div class="danger-zone" style="margin-top:24px">
  <h3>Danger zone</h3>
  <div class="actions">
    <form method="post" action="<?= admin_action('project_duplicate') ?>" class="inline-form">
      <?= csrf_field() ?><input type="hidden" name="id" value="<?= e($g['id']) ?>">
      <button class="btn ghost" type="submit">Duplicate project</button>
    </form>
    <form method="post" action="<?= admin_action('project_delete') ?>" class="inline-form">
      <?= csrf_field() ?><input type="hidden" name="id" value="<?= e($g['id']) ?>">
      <button class="btn danger" type="submit" data-confirm="Delete this project permanently? A revision will be kept so it can be restored.">Delete project</button>
    </form>
  </div>
</div>
<?php endif; ?>
