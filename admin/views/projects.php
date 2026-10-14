<?php /** Projects list. Vars: $groups */ ?>
<div class="toolbar">
  <div class="searchbar" style="margin:0">
    <input type="search" id="q" placeholder="Search title, location…" data-table-filter="projTbl" aria-label="Search projects">
    <select data-table-cat="projTbl" aria-label="Filter by status">
      <option value="">All statuses</option>
      <option value="published">Published</option><option value="draft">Draft</option><option value="archived">Archived</option>
    </select>
  </div>
  <?php if (can('projects')): ?><a class="btn" href="<?= admin_url('project_edit') ?>">+ New project</a><?php endif; ?>
</div>

<div class="card" style="padding:0;overflow:hidden">
<table class="tbl" id="projTbl">
  <thead><tr><th>#</th><th></th><th>Title</th><th>Location</th><th>Category</th><th>Status</th><th>Chapters</th><th></th></tr></thead>
  <tbody>
  <?php foreach ($groups as $g): $st = project_status($g); ?>
    <tr data-status="<?= $st ?>">
      <td><?= (int)($g['number'] ?? 0) ?></td>
      <td><img class="thumb-sm" src="../dist/assets/<?= e($g['hero'] ?? '') ?>.webp" alt="" loading="lazy" onerror="this.style.visibility='hidden'"></td>
      <td><strong><?= e($g['title'] ?? '') ?></strong><br><span style="color:#6B6E68;font-size:.82rem;font-family:ui-monospace,monospace"><?= e($g['id']) ?></span></td>
      <td><?= e($g['location'] ?? '') ?></td>
      <td><?= e($g['category'] ?? '') ?></td>
      <td><span class="pill <?= $st ?>"><?= $st ?></span></td>
      <td><?= count($g['slides'] ?? []) ?></td>
      <td style="white-space:nowrap">
        <?php if (can('projects')): ?><a class="btn small ghost" href="<?= admin_url('project_edit', ['id' => $g['id']]) ?>">Edit</a><?php endif; ?>
        <?php if (can('projects_delete')): ?>
          <form method="post" action="<?= admin_action('project_duplicate') ?>" class="inline-form">
            <?= csrf_field() ?><input type="hidden" name="id" value="<?= e($g['id']) ?>">
            <button class="btn small ghost" type="submit">Duplicate</button>
          </form>
        <?php endif; ?>
      </td>
    </tr>
  <?php endforeach; ?>
  </tbody>
</table>
</div>
<p style="color:#6B6E68;font-size:.86rem">Delete and revision history are available inside the project editor. The <strong>#</strong> column (featured order) is edited per project.</p>
