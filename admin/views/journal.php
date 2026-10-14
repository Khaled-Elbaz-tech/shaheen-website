<?php /** Journal CRUD. Vars: $journal */ ?>
<div class="card">
  <h2><?= isset($_GET['edit']) ? 'Edit entry' : 'New entry' ?></h2>
  <?php
    $ei = isset($_GET['edit']) ? (int)$_GET['edit'] : null;
    $je = ($ei !== null && isset($journal[$ei])) ? $journal[$ei] : ['title' => '', 'date' => '', 'summary' => '', 'link' => '', 'status' => 'published'];
  ?>
  <form method="post" action="<?= admin_action('journal_save') ?>">
    <?= csrf_field() ?>
    <?php if ($ei !== null): ?><input type="hidden" name="idx" value="<?= $ei ?>"><?php endif; ?>
    <div class="row">
      <div class="field"><label for="j-title">Title</label><input type="text" id="j-title" name="title" value="<?= e($je['title']) ?>" required maxlength="200"></div>
      <div class="field"><label for="j-date">Date</label><input type="date" id="j-date" name="date" value="<?= e($je['date']) ?>"></div>
    </div>
    <div class="field"><label for="j-summary">Summary</label><textarea id="j-summary" name="summary"><?= e($je['summary']) ?></textarea></div>
    <div class="row">
      <div class="field"><label for="j-link">Link (optional)</label><input type="url" id="j-link" name="link" value="<?= e($je['link']) ?>" placeholder="https://…"><span class="hint">External links only; javascript: URLs are blocked.</span></div>
      <div class="field"><label for="j-status">Status</label>
        <select id="j-status" name="status">
          <option value="published"<?= ($je['status'] ?? '') === 'published' ? ' selected' : '' ?>>Published</option>
          <option value="draft"<?= ($je['status'] ?? '') === 'draft' ? ' selected' : '' ?>>Draft (hidden from site)</option>
        </select></div>
    </div>
    <div class="actions">
      <button class="btn" type="submit"><?= $ei !== null ? 'Save changes' : 'Add entry' ?></button>
      <?php if ($ei !== null): ?><a class="btn ghost" href="<?= admin_url('journal') ?>">Cancel</a><?php endif; ?>
    </div>
  </form>
</div>

<div class="card" style="padding:0;overflow:hidden">
<table class="tbl">
  <thead><tr><th>Date</th><th>Title</th><th>Status</th><th></th></tr></thead>
  <tbody>
  <?php if (!$journal): ?>
    <tr><td colspan="4"><div class="list-empty"><p>No journal entries yet.</p></div></td></tr>
  <?php endif; ?>
  <?php foreach ($journal as $i => $j): ?>
    <tr>
      <td style="white-space:nowrap"><?= e($j['date'] ?: '—') ?></td>
      <td><strong><?= e($j['title']) ?></strong><br><span style="color:#6B6E68;font-size:.85rem"><?= e(trunc($j['summary'] ?? '', 90)) ?></span>
        <?php if (!empty($j['link'])): ?><br><a href="<?= e($j['link']) ?>" target="_blank" rel="noopener" style="font-size:.82rem">↗ <?= e(trunc($j['link'], 50)) ?></a><?php endif; ?></td>
      <td><span class="pill <?= e($j['status'] ?? 'published') ?>"><?= e($j['status'] ?? 'published') ?></span></td>
      <td style="white-space:nowrap">
        <a class="btn small ghost" href="<?= admin_url('journal', ['edit' => $i]) ?>">Edit</a>
        <form method="post" action="<?= admin_action('journal_delete') ?>" class="inline-form">
          <?= csrf_field() ?><input type="hidden" name="idx" value="<?= $i ?>">
          <button class="btn small danger" type="submit" data-confirm="Delete this entry?">Delete</button>
        </form>
      </td>
    </tr>
  <?php endforeach; ?>
  </tbody>
</table>
</div>
