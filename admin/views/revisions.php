<?php /** Revision history + restore. Vars: $group, $revisions */ ?>
<div class="card">
  <h2><?= e($group['title'] ?? $group['id']) ?> <span style="color:#6B6E68;font-weight:400;font-size:.85rem"><?= e($group['id']) ?></span></h2>
  <p class="lede">Restoring replaces the current project with the saved version. The current version is kept as a new revision first, so nothing is lost.</p>
  <?php if (!$revisions): ?>
    <div class="list-empty"><p>No revisions yet — they are created automatically each time the project is saved.</p></div>
  <?php else: ?>
  <table class="tbl">
    <thead><tr><th>#</th><th>Saved</th><th>By</th><th>Summary</th><th></th></tr></thead>
    <tbody>
    <?php foreach ($revisions as $r):
      $d = json_decode($r['data'], true) ?: [];
    ?>
      <tr>
        <td><?= (int)$r['id'] ?></td>
        <td style="white-space:nowrap"><?= e(fmt_dt($r['created_at'])) ?></td>
        <td><?= e($r['user_name'] ?? '—') ?></td>
        <td><?= e(trunc($d['title'] ?? '', 40)) ?> · <?= count($d['slides'] ?? []) ?> chapters · <span class="pill <?= e($d['status'] ?? 'published') ?>"><?= e($d['status'] ?? 'published') ?></span></td>
        <td>
          <form method="post" action="<?= admin_action('project_restore') ?>" class="inline-form">
            <?= csrf_field() ?><input type="hidden" name="revision_id" value="<?= (int)$r['id'] ?>">
            <button class="btn small ghost" type="submit" data-confirm="Restore this version? The current version will be kept as a revision.">Restore</button>
          </form>
        </td>
      </tr>
    <?php endforeach; ?>
    </tbody>
  </table>
  <?php endif; ?>
  <p><a href="<?= admin_url('project_edit', ['id' => $group['id']]) ?>">← Back to editor</a></p>
</div>
