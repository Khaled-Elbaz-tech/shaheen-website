<?php /** Activity log. Vars: $rows */ ?>
<div class="toolbar">
  <div class="searchbar" style="margin:0"><input type="search" placeholder="Search actions, users, details…" data-table-filter="actTbl" aria-label="Search activity"></div>
  <span style="color:#6B6E68;font-size:.88rem"><?= count($rows) ?> entries (latest 200)</span>
</div>
<div class="card" style="padding:0;overflow:hidden">
<table class="tbl" id="actTbl">
  <thead><tr><th>When</th><th>User</th><th>Action</th><th>Detail</th><th>IP</th></tr></thead>
  <tbody>
  <?php if (!$rows): ?><tr><td colspan="5"><div class="list-empty"><p>No activity logged yet.</p></div></td></tr><?php endif; ?>
  <?php foreach ($rows as $r): ?>
    <tr>
      <td style="white-space:nowrap"><?= e(fmt_dt($r['created_at'])) ?></td>
      <td><?= e($r['user_name'] ?? '—') ?></td>
      <td><code><?= e($r['action']) ?></code></td>
      <td><?= e(trunc($r['detail'] ?? '', 120)) ?></td>
      <td style="color:#6B6E68;font-size:.85rem"><?= e($r['ip'] ?? '') ?></td>
    </tr>
  <?php endforeach; ?>
  </tbody>
</table>
</div>
